"""gr.WebRTC() component."""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import threading
import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generator,
    Iterable,
    Literal,
    ParamSpec,
    Sequence,
    TypeAlias,
    TypeVar,
    Union,
    cast,
)

import anyio.to_thread
import av
import numpy as np
from aiortc import (
    AudioStreamTrack,
    MediaStreamTrack,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import AudioFrame, MediaRelay, VideoFrame  # type: ignore
from aiortc.mediastreams import MediaStreamError
from gradio import wasm_utils
from gradio.components.base import Component, server
from gradio_client import handle_file
from numpy import typing as npt

from gradio_webrtc.utils import (
    AdditionalOutputs,
    DataChannel,
    current_channel,
    player_worker_decode,
    split_output,
)

if TYPE_CHECKING:
    from gradio.blocks import Block
    from gradio.components import Timer
    from gradio.events import Dependency


if wasm_utils.IS_WASM:
    raise ValueError("Not supported in gradio-lite!")


logger = logging.getLogger(__name__)

VideoEmitType = Union[
    AdditionalOutputs, tuple[npt.ArrayLike, AdditionalOutputs], npt.ArrayLike, None
]
VideoEventHandler = Callable[[npt.ArrayLike], VideoEmitType]


class VideoCallback(VideoStreamTrack):
    """
    This works for streaming input and output
    """

    kind = "video"

    def __init__(
        self,
        track: MediaStreamTrack,
        event_handler: VideoEventHandler,
        channel: DataChannel | None = None,
        set_additional_outputs: Callable | None = None,
        mode: Literal["send-receive", "send"] = "send-receive",
    ) -> None:
        super().__init__()  # don't forget this!
        self.track = track
        self.event_handler = event_handler
        self.latest_args: str | list[Any] = "not_set"
        self.channel = channel
        self.set_additional_outputs = set_additional_outputs
        self.thread_quit = asyncio.Event()
        self.mode = mode
        self.channel_set = asyncio.Event()
        self.has_started = False

    def set_channel(self, channel: DataChannel):
        self.channel = channel
        current_channel.set(channel)
        self.channel_set.set()

    def set_args(self, args: list[Any]):
        self.latest_args = ["__webrtc_value__"] + list(args)

    def add_frame_to_payload(
        self, args: list[Any], frame: np.ndarray | None
    ) -> list[Any]:
        new_args = []
        for val in args:
            if isinstance(val, str) and val == "__webrtc_value__":
                new_args.append(frame)
            else:
                new_args.append(val)
        return new_args

    def array_to_frame(self, array: np.ndarray) -> VideoFrame:
        return VideoFrame.from_ndarray(array, format="bgr24")

    async def process_frames(self):
        while not self.thread_quit.is_set():
            try:
                await self.recv()
            except TimeoutError:
                continue

    def start(
        self,
    ):
        asyncio.create_task(self.process_frames())

    def stop(self):
        super().stop()
        logger.debug("video callback stop")
        self.thread_quit.set()

    async def wait_for_channel(self):
        if not self.channel_set.is_set():
            await self.channel_set.wait()
        if current_channel.get() != self.channel:
            current_channel.set(self.channel)

    async def recv(self):  # type: ignore
        try:
            try:
                frame = cast(VideoFrame, await self.track.recv())
            except MediaStreamError:
                self.stop()
                return

            await self.wait_for_channel()
            frame_array = frame.to_ndarray(format="bgr24")
            if self.latest_args == "not_set":
                return frame

            args = self.add_frame_to_payload(cast(list, self.latest_args), frame_array)

            array, outputs = split_output(self.event_handler(*args))
            if (
                isinstance(outputs, AdditionalOutputs)
                and self.set_additional_outputs
                and self.channel
            ):
                self.set_additional_outputs(outputs)
                self.channel.send("change")
            if array is None and self.mode == "send":
                return

            new_frame = self.array_to_frame(array)
            if frame:
                new_frame.pts = frame.pts
                new_frame.time_base = frame.time_base
            else:
                pts, time_base = await self.next_timestamp()
                new_frame.pts = pts
                new_frame.time_base = time_base

            return new_frame
        except Exception as e:
            logger.debug("exception %s", e)
            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)


class StreamHandlerBase(ABC):
    def __init__(
        self,
        expected_layout: Literal["mono", "stereo"] = "mono",
        output_sample_rate: int = 24000,
        output_frame_size: int = 960,
        input_sample_rate: int = 48000,
    ) -> None:
        self.expected_layout = expected_layout
        self.output_sample_rate = output_sample_rate
        self.output_frame_size = output_frame_size
        self.input_sample_rate = input_sample_rate
        self.latest_args: list[Any] = []
        self._resampler = None
        self._channel: DataChannel | None = None
        self._loop: asyncio.AbstractEventLoop
        self.args_set = asyncio.Event()
        self.channel_set = asyncio.Event()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return cast(asyncio.AbstractEventLoop, self._loop)

    @property
    def channel(self) -> DataChannel | None:
        return self._channel

    def set_channel(self, channel: DataChannel):
        self._channel = channel
        self.channel_set.set()

    async def fetch_args(
        self,
    ):
        if self.channel:
            self.channel.send("tick")
            logger.debug("Sent tick")

    async def wait_for_args(self):
        await self.fetch_args()
        await self.args_set.wait()

    def wait_for_args_sync(self):
        asyncio.run_coroutine_threadsafe(self.wait_for_args(), self.loop).result()

    def set_args(self, args: list[Any]):
        logger.debug("setting args in audio callback %s", args)
        self.latest_args = ["__webrtc_value__"] + list(args)
        self.args_set.set()

    def reset(self):
        self.args_set.clear()

    def shutdown(self):
        pass

    @abstractmethod
    def copy(self) -> "StreamHandlerBase":
        pass

    def resample(self, frame: AudioFrame) -> Generator[AudioFrame, None, None]:
        if self._resampler is None:
            self._resampler = av.AudioResampler(  # type: ignore
                format="s16",
                layout=self.expected_layout,
                rate=self.input_sample_rate,
                frame_size=frame.samples,
            )
        yield from self._resampler.resample(frame)


EmitType: TypeAlias = Union[
    tuple[int, np.ndarray],
    tuple[int, np.ndarray, Literal["mono", "stereo"]],
    AdditionalOutputs,
    tuple[tuple[int, np.ndarray], AdditionalOutputs],
    None,
]
AudioEmitType = EmitType


class StreamHandler(StreamHandlerBase):
    @abstractmethod
    def receive(self, frame: tuple[int, np.ndarray]) -> None:
        pass

    @abstractmethod
    def emit(
        self,
    ) -> EmitType:
        pass


class AsyncStreamHandler(StreamHandlerBase):
    @abstractmethod
    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        pass

    @abstractmethod
    async def emit(
        self,
    ) -> EmitType:
        pass


StreamHandlerImpl = Union[StreamHandler, AsyncStreamHandler]


class AudioVideoStreamHandler(StreamHandlerBase):
    @abstractmethod
    def video_receive(self, frame: npt.NDArray) -> None:
        pass

    @abstractmethod
    def video_emit(
        self,
    ) -> VideoEmitType:
        pass


class AsyncAudioVideoStreamHandler(StreamHandlerBase):
    @abstractmethod
    async def video_receive(self, frame: npt.NDArray) -> None:
        pass

    @abstractmethod
    async def video_emit(
        self,
    ) -> VideoEmitType:
        pass


VideoStreamHandlerImpl = Union[AudioVideoStreamHandler, AsyncAudioVideoStreamHandler]
AudioVideoStreamHandlerImpl = Union[
    AudioVideoStreamHandler, AsyncAudioVideoStreamHandler
]
AsyncHandler = Union[AsyncStreamHandler, AsyncAudioVideoStreamHandler]


class VideoStreamHander(VideoCallback):
    async def process_frames(self):
        while not self.thread_quit.is_set():
            try:
                await self.channel_set.wait()
                frame = cast(VideoFrame, await self.track.recv())
                frame_array = frame.to_ndarray(format="bgr24")
                handler = cast(VideoStreamHandlerImpl, self.event_handler)
                if inspect.iscoroutinefunction(handler.video_receive):
                    await handler.video_receive(frame_array)
                else:
                    handler.video_receive(frame_array)
            except MediaStreamError:
                self.stop()

    def start(self):
        if not self.has_started:
            asyncio.create_task(self.process_frames())
            self.has_started = True

    async def recv(self):  # type: ignore
        self.start()
        try:
            handler = cast(VideoStreamHandlerImpl, self.event_handler)
            if inspect.iscoroutinefunction(handler.video_emit):
                outputs = await handler.video_emit()
            else:
                outputs = handler.video_emit()

            array, outputs = split_output(outputs)
            if (
                isinstance(outputs, AdditionalOutputs)
                and self.set_additional_outputs
                and self.channel
            ):
                self.set_additional_outputs(outputs)
                self.channel.send("change")
            if array is None and self.mode == "send":
                return

            new_frame = self.array_to_frame(array)

            # Will probably have to give developer ability to set pts and time_base
            pts, time_base = await self.next_timestamp()
            new_frame.pts = pts
            new_frame.time_base = time_base

            return new_frame
        except Exception as e:
            logger.debug("exception %s", e)
            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)


class AudioCallback(AudioStreamTrack):
    kind = "audio"

    def __init__(
        self,
        track: MediaStreamTrack,
        event_handler: StreamHandlerBase,
        channel: DataChannel | None = None,
        set_additional_outputs: Callable | None = None,
    ) -> None:
        super().__init__()
        self.track = track
        self.event_handler = cast(StreamHandlerImpl, event_handler)
        self.current_timestamp = 0
        self.latest_args: str | list[Any] = "not_set"
        self.queue = asyncio.Queue()
        self.thread_quit = asyncio.Event()
        self._start: float | None = None
        self.has_started = False
        self.last_timestamp = 0
        self.channel = channel
        self.set_additional_outputs = set_additional_outputs

    def set_channel(self, channel: DataChannel):
        self.channel = channel
        self.event_handler.set_channel(channel)

    def set_args(self, args: list[Any]):
        self.event_handler.set_args(args)

    def event_handler_receive(self, frame: tuple[int, np.ndarray]) -> None:
        current_channel.set(self.event_handler.channel)
        return cast(Callable, self.event_handler.receive)(frame)

    async def process_input_frames(self) -> None:
        while not self.thread_quit.is_set():
            try:
                frame = cast(AudioFrame, await self.track.recv())
                for frame in self.event_handler.resample(frame):
                    numpy_array = frame.to_ndarray()
                    if isinstance(self.event_handler, AsyncHandler):
                        await self.event_handler.receive(
                            (frame.sample_rate, numpy_array)
                        )
                    else:
                        await anyio.to_thread.run_sync(
                            self.event_handler_receive, (frame.sample_rate, numpy_array)
                        )
            except MediaStreamError:
                logger.debug("MediaStreamError in process_input_frames")
                break

    def start(self):
        if not self.has_started:
            loop = asyncio.get_running_loop()
            if isinstance(self.event_handler, AsyncHandler):
                callable = self.event_handler.emit
            else:
                callable = functools.partial(
                    loop.run_in_executor, None, self.event_handler.emit
                )
            asyncio.create_task(self.process_input_frames())
            asyncio.create_task(
                player_worker_decode(
                    callable,
                    self.queue,
                    self.thread_quit,
                    lambda: self.channel,
                    self.set_additional_outputs,
                    False,
                    self.event_handler.output_sample_rate,
                    self.event_handler.output_frame_size,
                )
            )
            self.has_started = True

    async def recv(self):  # type: ignore
        try:
            if self.readyState != "live":
                raise MediaStreamError

            if not self.event_handler.channel_set.is_set():
                await self.event_handler.channel_set.wait()
            if current_channel.get() != self.event_handler.channel:
                current_channel.set(self.event_handler.channel)

            self.start()

            frame = await self.queue.get()
            logger.debug("frame %s", frame)

            data_time = frame.time

            if time.time() - self.last_timestamp > 10 * (
                self.event_handler.output_frame_size
                / self.event_handler.output_sample_rate
            ):
                self._start = None

            # control playback rate
            if self._start is None:
                self._start = time.time() - data_time  # type: ignore
            else:
                wait = self._start + data_time - time.time()
                await asyncio.sleep(wait)
            self.last_timestamp = time.time()
            return frame
        except Exception as e:
            logger.debug("exception %s", e)
            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)

    def stop(self):
        logger.debug("audio callback stop")
        self.thread_quit.set()
        super().stop()

    def shutdown(self):
        self.event_handler.shutdown()


class ServerToClientVideo(VideoStreamTrack):
    """
    This works for streaming input and output
    """

    kind = "video"

    def __init__(
        self,
        event_handler: Callable,
        channel: DataChannel | None = None,
        set_additional_outputs: Callable | None = None,
    ) -> None:
        super().__init__()  # don't forget this!
        self.event_handler = event_handler
        self.args_set = asyncio.Event()
        self.latest_args: str | list[Any] = "not_set"
        self.generator: Generator[Any, None, Any] | None = None
        self.channel = channel
        self.set_additional_outputs = set_additional_outputs

    def array_to_frame(self, array: np.ndarray) -> VideoFrame:
        return VideoFrame.from_ndarray(array, format="bgr24")

    def set_channel(self, channel: DataChannel):
        self.channel = channel

    def set_args(self, args: list[Any]):
        self.latest_args = list(args)
        self.args_set.set()

    async def recv(self):  # type: ignore
        try:
            pts, time_base = await self.next_timestamp()
            await self.args_set.wait()
            if self.generator is None:
                self.generator = cast(
                    Generator[Any, None, Any], self.event_handler(*self.latest_args)
                )
                current_channel.set(self.channel)
            try:
                next_array, outputs = split_output(next(self.generator))
                if (
                    isinstance(outputs, AdditionalOutputs)
                    and self.set_additional_outputs
                    and self.channel
                ):
                    self.set_additional_outputs(outputs)
                    self.channel.send("change")
            except StopIteration:
                self.stop()
                return

            next_frame = self.array_to_frame(next_array)
            next_frame.pts = pts
            next_frame.time_base = time_base
            return next_frame
        except Exception as e:
            logger.debug("exception %s", e)
            exec = traceback.format_exc()
            logger.debug("traceback %s ", exec)


class ServerToClientAudio(AudioStreamTrack):
    kind = "audio"

    def __init__(
        self,
        event_handler: Callable,
        channel: DataChannel | None = None,
        set_additional_outputs: Callable | None = None,
    ) -> None:
        self.generator: Generator[Any, None, Any] | None = None
        self.event_handler = event_handler
        self.current_timestamp = 0
        self.latest_args: str | list[Any] = "not_set"
        self.args_set = threading.Event()
        self.queue = asyncio.Queue()
        self.thread_quit = asyncio.Event()
        self.channel = channel
        self.set_additional_outputs = set_additional_outputs
        self.has_started = False
        self._start: float | None = None
        super().__init__()

    def set_channel(self, channel: DataChannel):
        self.channel = channel

    def set_args(self, args: list[Any]):
        self.latest_args = list(args)
        self.args_set.set()

    def next(self) -> tuple[int, np.ndarray] | None:
        self.args_set.wait()
        current_channel.set(self.channel)
        if self.generator is None:
            self.generator = self.event_handler(*self.latest_args)
        if self.generator is not None:
            try:
                frame = next(self.generator)
                return frame
            except StopIteration:
                self.thread_quit.set()

    def start(self):
        if not self.has_started:
            loop = asyncio.get_running_loop()
            callable = functools.partial(loop.run_in_executor, None, self.next)
            asyncio.create_task(
                player_worker_decode(
                    callable,
                    self.queue,
                    self.thread_quit,
                    lambda: self.channel,
                    self.set_additional_outputs,
                    True,
                )
            )
            self.has_started = True

    async def recv(self):  # type: ignore
        try:
            if self.readyState != "live":
                raise MediaStreamError

            self.start()
            data = await self.queue.get()
            if data is None:
                self.stop()
                return

            data_time = data.time

            # control playback rate
            if data_time is not None:
                if self._start is None:
                    self._start = time.time() - data_time  # type: ignore
                else:
                    wait = self._start + data_time - time.time()
                    await asyncio.sleep(wait)

            return data
        except Exception as e:
            logger.debug("exception %s", e)
            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)

    def stop(self):
        logger.debug("audio-to-client stop callback")
        self.thread_quit.set()
        super().stop()


# For the return type
R = TypeVar("R")
# For the parameter specification
P = ParamSpec("P")


class WebRTC(Component):
    """
    Creates a video component that can be used to upload/record videos (as an input) or display videos (as an output).
    For the video to be playable in the browser it must have a compatible container and codec combination. Allowed
    combinations are .mp4 with h264 codec, .ogg with theora codec, and .webm with vp9 codec. If the component detects
    that the output video would not be playable in the browser it will attempt to convert it to a playable mp4 video.
    If the conversion fails, the original video is returned.

    Demos: video_identity_2
    """

    pcs: set[RTCPeerConnection] = set([])
    relay = MediaRelay()
    connections: dict[
        str,
        list[VideoCallback | ServerToClientVideo | ServerToClientAudio | AudioCallback],
    ] = defaultdict(list)
    data_channels: dict[str, DataChannel] = {}
    additional_outputs: dict[str, list[AdditionalOutputs]] = {}
    handlers: dict[str, StreamHandlerBase | Callable] = {}

    EVENTS = ["tick", "state_change"]

    def __init__(
        self,
        value: None = None,
        height: int | str | None = None,
        width: int | str | None = None,
        label: str | None = None,
        every: Timer | float | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        show_label: bool | None = None,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | None = None,
        mirror_webcam: bool = True,
        rtc_configuration: dict[str, Any] | None = None,
        track_constraints: dict[str, Any] | None = None,
        time_limit: float | None = None,
        mode: Literal["send-receive", "receive", "send"] = "send-receive",
        modality: Literal["video", "audio", "audio-video"] = "video",
        rtp_params: dict[str, Any] | None = None,
        icon: str | None = None,
        icon_button_color: str | None = None,
        pulse_color: str | None = None,
    ):
        """
        Parameters:
            value: path or URL for the default value that WebRTC component is going to take. Can also be a tuple consisting of (video filepath, subtitle filepath). If a subtitle file is provided, it should be of type .srt or .vtt. Or can be callable, in which case the function will be called whenever the app loads to set the initial value of the component.
            format: the file extension with which to save video, such as 'avi' or 'mp4'. This parameter applies both when this component is used as an input to determine which file format to convert user-provided video to, and when this component is used as an output to determine the format of video returned to the user. If None, no file format conversion is done and the video is kept as is. Use 'mp4' to ensure browser playability.
            height: The height of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.
            width: The width of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.
            label: the label for this component. Appears above the component and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component is assigned to.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            inputs: components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise). `value` is recalculated any time the inputs change.
            show_label: if True, will display label.
            container: if True, will place the component in a container - providing some extra padding around the border.
            scale: relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.
            min_width: minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.
            interactive: if True, will allow users to upload a video; if False, can only be used to display videos. If not provided, this is inferred based on whether the component is used as an input or output.
            visible: if False, component will be hidden.
            elem_id: an optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.
            elem_classes: an optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.
            render: if False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.
            key: if assigned, will be used to assume identity across a re-render. Components that have the same key across a re-render will have their value preserved.
            mirror_webcam: if True webcam will be mirrored. Default is True.
            rtc_configuration: WebRTC configuration options. See https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/RTCPeerConnection . If running the demo on a remote server, you will need to specify a rtc_configuration. See https://freddyaboulton.github.io/gradio-webrtc/deployment/
            track_constraints: Media track constraints for WebRTC. For example, to set video height, width use {"width": {"exact": 800}, "height": {"exact": 600}, "aspectRatio": {"exact": 1.33333}}
            time_limit: Maximum duration in seconds for recording.
            mode: WebRTC mode - "send-receive", "receive", or "send".
            modality: Type of media - "video" or "audio".
            rtp_params: See https://developer.mozilla.org/en-US/docs/Web/API/RTCRtpSender/setParameters. If you are changing the video resolution, you can set this to {"degradationPreference": "maintain-framerate"} to keep the frame rate consistent.
            icon: Icon to display on the button instead of the wave animation. The icon should be a path/url to a .svg/.png/.jpeg file.
            icon_button_color: Color of the icon button. Default is var(--color-accent) of the demo theme.
            pulse_color: Color of the pulse animation. Default is var(--color-accent) of the demo theme.
        """
        self.time_limit = time_limit
        self.height = height
        self.width = width
        self.mirror_webcam = mirror_webcam
        self.concurrency_limit = 1
        self.rtc_configuration = rtc_configuration
        self.mode = mode
        self.modality = modality
        self.icon_button_color = icon_button_color
        self.pulse_color = pulse_color
        self.rtp_params = rtp_params or {}
        if track_constraints is None and modality == "audio":
            track_constraints = {
                "echoCancellation": True,
                "noiseSuppression": {"exact": True},
                "autoGainControl": {"exact": True},
                "sampleRate": {"ideal": 24000},
                "sampleSize": {"ideal": 16},
                "channelCount": {"exact": 1},
            }
        if track_constraints is None and modality == "video":
            track_constraints = {
                "facingMode": "user",
                "width": {"ideal": 500},
                "height": {"ideal": 500},
                "frameRate": {"ideal": 30},
            }
        if track_constraints is None and modality == "audio-video":
            track_constraints = {
                "video": {
                    "facingMode": "user",
                    "width": {"ideal": 500},
                    "height": {"ideal": 500},
                    "frameRate": {"ideal": 30},
                },
                "audio": {
                    "echoCancellation": True,
                    "noiseSuppression": {"exact": True},
                    "autoGainControl": {"exact": True},
                    "sampleRate": {"ideal": 24000},
                    "sampleSize": {"ideal": 16},
                    "channelCount": {"exact": 1},
                },
            }
        self.track_constraints = track_constraints
        self.event_handler: Callable | StreamHandler | None = None
        super().__init__(
            label=label,
            every=every,
            inputs=inputs,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            key=key,
            value=value,
        )
        # need to do this here otherwise the proxy_url is not set
        self.icon = (
            icon if not icon else cast(dict, self.serve_static_file(icon)).get("url")
        )

    def set_additional_outputs(
        self, webrtc_id: str
    ) -> Callable[[AdditionalOutputs], None]:
        def set_outputs(outputs: AdditionalOutputs):
            if webrtc_id not in self.additional_outputs:
                self.additional_outputs[webrtc_id] = []
            self.additional_outputs[webrtc_id].append(outputs)

        return set_outputs

    def preprocess(self, payload: str) -> str:
        """
        Parameters:
            payload: An instance of VideoData containing the video and subtitle files.
        Returns:
            Passes the uploaded video as a `str` filepath or URL whose extension can be modified by `format`.
        """
        return payload

    def postprocess(self, value: Any) -> str:
        """
        Parameters:
            value: Expects a {str} or {pathlib.Path} filepath to a video which is displayed, or a {Tuple[str | pathlib.Path, str | pathlib.Path | None]} where the first element is a filepath to a video and the second element is an optional filepath to a subtitle file.
        Returns:
            VideoData object containing the video and subtitle files.
        """
        return value

    def set_input(self, webrtc_id: str, *args):
        if webrtc_id in self.connections:
            for conn in self.connections[webrtc_id]:
                conn.set_args(list(args))

    def on_additional_outputs(
        self,
        fn: Callable[Concatenate[P], R],
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | set[Block] | None = None,
        js: str | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        queue: bool = True,
    ):
        inputs = inputs or []
        if inputs and not isinstance(inputs, Iterable):
            inputs = [inputs]
            inputs = list(inputs)

        def handler(webrtc_id: str, *args):
            if (
                webrtc_id in self.additional_outputs
                and len(self.additional_outputs[webrtc_id]) > 0
            ):
                next_outputs = self.additional_outputs[webrtc_id].pop(0)
                return fn(*args, *next_outputs.args)  # type: ignore
            return (
                tuple([None for _ in range(len(outputs))])
                if isinstance(outputs, Iterable)
                else None
            )

        return self.state_change(  # type: ignore
            fn=handler,
            inputs=[self] + cast(list, inputs),
            outputs=outputs,
            js=js,
            concurrency_limit=concurrency_limit,
            concurrency_id=concurrency_id,
            show_progress=show_progress,
            queue=queue,
            trigger_mode="multiple",
        )

    def stream(
        self,
        fn: Callable[..., Any]
        | StreamHandlerImpl
        | AudioVideoStreamHandlerImpl
        | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | set[Block] | None = None,
        js: str | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        time_limit: float | None = None,
        trigger: Dependency | None = None,
    ):
        from gradio.blocks import Block

        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        if isinstance(inputs, Block):
            inputs = [inputs]
        if isinstance(outputs, Block):
            outputs = [outputs]

        self.concurrency_limit = (
            1 if concurrency_limit in ["default", None] else concurrency_limit
        )
        self.event_handler = fn  # type: ignore
        self.time_limit = time_limit

        if (
            self.mode == "send-receive"
            and self.modality in ["audio", "audio-video"]
            and not isinstance(self.event_handler, StreamHandlerBase)
        ):
            raise ValueError(
                "In the send-receive mode for audio, the event handler must be an instance of StreamHandlerBase."
            )

        if self.mode == "send-receive" or self.mode == "send":
            if cast(list[Block], inputs)[0] != self:
                raise ValueError(
                    "In the webrtc stream event, the first input component must be the WebRTC component."
                )

            if (
                len(cast(list[Block], outputs)) != 1
                and cast(list[Block], outputs)[0] != self
            ):
                raise ValueError(
                    "In the webrtc stream event, the only output component must be the WebRTC component."
                )
            for input_component in inputs[1:]:  # type: ignore
                if hasattr(input_component, "change"):
                    input_component.change(  # type: ignore
                        self.set_input,
                        inputs=inputs,
                        outputs=None,
                        concurrency_id=concurrency_id,
                        concurrency_limit=None,
                        time_limit=None,
                        js=js,
                    )
            return self.tick(  # type: ignore
                self.set_input,
                inputs=inputs,
                outputs=None,
                concurrency_id=concurrency_id,
                concurrency_limit=None,
                time_limit=None,
                js=js,
            )
        elif self.mode == "receive":
            if isinstance(inputs, list) and self in cast(list[Block], inputs):
                raise ValueError(
                    "In the receive mode stream event, the WebRTC component cannot be an input."
                )
            if (
                len(cast(list[Block], outputs)) != 1
                and cast(list[Block], outputs)[0] != self
            ):
                raise ValueError(
                    "In the receive mode stream, the only output component must be the WebRTC component."
                )
            if trigger is None:
                raise ValueError(
                    "In the receive mode stream event, the trigger parameter must be provided"
                )
            trigger(lambda: "start_webrtc_stream", inputs=None, outputs=self)
            self.tick(  # type: ignore
                self.set_input,
                inputs=[self] + list(inputs),
                outputs=None,
                concurrency_id=concurrency_id,
            )

    @staticmethod
    async def wait_for_time_limit(pc: RTCPeerConnection, time_limit: float):
        await asyncio.sleep(time_limit)
        await pc.close()

    def clean_up(self, webrtc_id: str):
        self.handlers.pop(webrtc_id, None)
        connection = self.connections.pop(webrtc_id, [])
        for conn in connection:
            if isinstance(conn, AudioCallback):
                conn.event_handler.shutdown()
        self.additional_outputs.pop(webrtc_id, None)
        self.data_channels.pop(webrtc_id, None)
        return connection

    @server
    async def offer(self, body):
        logger.debug("Starting to handle offer")
        logger.debug("Offer body %s", body)
        if len(self.connections) >= cast(int, self.concurrency_limit):
            return {"status": "failed"}

        offer = RTCSessionDescription(sdp=body["sdp"], type=body["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        if isinstance(self.event_handler, StreamHandlerBase):
            handler = self.event_handler.copy()
        else:
            handler = cast(Callable, self.event_handler)

        self.handlers[body["webrtc_id"]] = handler

        set_outputs = self.set_additional_outputs(body["webrtc_id"])

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.debug("ICE connection state change %s", pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.connections.pop(body["webrtc_id"], None)
                self.pcs.discard(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.debug("pc.connectionState %s", pc.connectionState)
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                connection = self.clean_up(body["webrtc_id"])
                if connection:
                    for conn in connection:
                        conn.stop()
                self.pcs.discard(pc)
            if pc.connectionState == "connected":
                if self.time_limit is not None:
                    asyncio.create_task(self.wait_for_time_limit(pc, self.time_limit))

        @pc.on("track")
        def on_track(track):
            relay = MediaRelay()
            handler = self.handlers[body["webrtc_id"]]

            if self.modality == "video" and track.kind == "video":
                cb = VideoCallback(
                    relay.subscribe(track),
                    event_handler=cast(VideoEventHandler, handler),
                    set_additional_outputs=set_outputs,
                    mode=cast(Literal["send", "send-receive"], self.mode),
                )
            elif self.modality == "audio-video" and track.kind == "video":
                cb = VideoStreamHander(
                    relay.subscribe(track),
                    event_handler=handler,  # type: ignore
                    set_additional_outputs=set_outputs,
                )
            elif self.modality in ["audio", "audio-video"] and track.kind == "audio":
                eh = cast(StreamHandlerImpl, handler)
                eh._loop = asyncio.get_running_loop()
                cb = AudioCallback(
                    relay.subscribe(track),
                    event_handler=eh,
                    set_additional_outputs=set_outputs,
                )
            else:
                raise ValueError("Modality must be either video, audio, or audio-video")
            if body["webrtc_id"] not in self.connections:
                self.connections[body["webrtc_id"]] = []

            self.connections[body["webrtc_id"]].append(cb)
            if body["webrtc_id"] in self.data_channels:
                for conn in self.connections[body["webrtc_id"]]:
                    conn.set_channel(self.data_channels[body["webrtc_id"]])
            if self.mode == "send-receive":
                logger.debug("Adding track to peer connection %s", cb)
                pc.addTrack(cb)
            elif self.mode == "send":
                cast(AudioCallback | VideoCallback, cb).start()

        if self.mode == "receive":
            if self.modality == "video":
                cb = ServerToClientVideo(
                    cast(Callable, self.event_handler),
                    set_additional_outputs=set_outputs,
                )
            elif self.modality == "audio":
                cb = ServerToClientAudio(
                    cast(Callable, self.event_handler),
                    set_additional_outputs=set_outputs,
                )
            else:
                raise ValueError("Modality must be either video or audio")

            logger.debug("Adding track to peer connection %s", cb)
            pc.addTrack(cb)
            self.connections[body["webrtc_id"]].append(cb)
            cb.on("ended", lambda: self.clean_up(body["webrtc_id"]))

        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.debug(f"Data channel established: {channel.label}")

            self.data_channels[body["webrtc_id"]] = channel

            async def set_channel(webrtc_id: str):
                while not self.connections.get(webrtc_id):
                    await asyncio.sleep(0.05)
                logger.debug("setting channel for webrtc id %s", webrtc_id)
                for conn in self.connections[webrtc_id]:
                    conn.set_channel(channel)

            asyncio.create_task(set_channel(body["webrtc_id"]))

            @channel.on("message")
            def on_message(message):
                logger.debug(f"Received message: {message}")
                if channel.readyState == "open":
                    channel.send(f"Server received: {message}")

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)  # type: ignore
        logger.debug("done handling offer about to return")
        await asyncio.sleep(0.1)

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
        }

    def example_payload(self) -> Any:
        return {
            "video": handle_file(
                "https://github.com/gradio-app/gradio/raw/main/demo/video_component/files/world.mp4"
            ),
        }

    def example_value(self) -> Any:
        return "https://github.com/gradio-app/gradio/raw/main/demo/video_component/files/world.mp4"

    def api_info(self) -> Any:
        return {"type": "number"}
