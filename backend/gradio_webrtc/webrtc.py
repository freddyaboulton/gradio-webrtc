"""gr.WebRTC() component."""

from __future__ import annotations

import asyncio
import functools
import logging
import threading
import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Generator, Literal, Sequence, cast

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

from gradio_webrtc.utils import player_worker_decode

if TYPE_CHECKING:
    from gradio.blocks import Block
    from gradio.components import Timer
    from gradio.events import Dependency


if wasm_utils.IS_WASM:
    raise ValueError("Not supported in gradio-lite!")


logger = logging.getLogger(__name__)


class VideoCallback(VideoStreamTrack):
    """
    This works for streaming input and output
    """

    kind = "video"

    def __init__(
        self,
        track: MediaStreamTrack,
        event_handler: Callable,
    ) -> None:
        super().__init__()  # don't forget this!
        self.track = track
        self.event_handler = event_handler
        self.latest_args: str | list[Any] = "not_set"

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

    async def recv(self):
        try:
            try:
                frame = cast(VideoFrame, await self.track.recv())
            except MediaStreamError:
                return
            frame_array = frame.to_ndarray(format="bgr24")

            if self.latest_args == "not_set":
                return frame

            args = self.add_frame_to_payload(cast(list, self.latest_args), frame_array)

            array = self.event_handler(*args)

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


class StreamHandler(ABC):
    def __init__(
        self,
        expected_layout: Literal["mono", "stereo"] = "mono",
        output_sample_rate: int = 24000,
        output_frame_size: int = 960,
    ) -> None:
        self.expected_layout = expected_layout
        self.output_sample_rate = output_sample_rate
        self.output_frame_size = output_frame_size
        self._resampler = None

    def copy(self) -> "StreamHandler":
        try:
            return deepcopy(self)
        except Exception:
            raise ValueError(
                "Current StreamHandler implementation cannot be deepcopied. Implement the copy method."
            )

    def resample(self, frame: AudioFrame) -> Generator[AudioFrame, None, None]:
        if self._resampler is None:
            self._resampler = av.AudioResampler(  # type: ignore
                format="s16",
                layout=self.expected_layout,
                rate=frame.sample_rate,
                frame_size=frame.samples,
            )
        yield from self._resampler.resample(frame)

    @abstractmethod
    def receive(self, frame: tuple[int, np.ndarray] | np.ndarray) -> None:
        pass

    @abstractmethod
    def emit(self) -> None:
        pass


class AudioCallback(AudioStreamTrack):
    kind = "audio"

    def __init__(
        self,
        track: MediaStreamTrack,
        event_handler: StreamHandler,
    ) -> None:
        self.track = track
        self.event_handler = event_handler
        self.current_timestamp = 0
        self.latest_args: str | list[Any] = "not_set"
        self.queue = asyncio.Queue()
        self.thread_quit = asyncio.Event()
        self._start: float | None = None
        self.has_started = False
        self.last_timestamp = 0
        super().__init__()

    async def process_input_frames(self) -> None:
        while not self.thread_quit.is_set():
            try:
                frame = cast(AudioFrame, await self.track.recv())
                for frame in self.event_handler.resample(frame):
                    numpy_array = frame.to_ndarray()
                    await anyio.to_thread.run_sync(
                        self.event_handler.receive, (frame.sample_rate, numpy_array)
                    )
            except MediaStreamError:
                logger.debug("MediaStreamError in process_input_frames")
                break

    def start(self):
        if not self.has_started:
            loop = asyncio.get_running_loop()
            callable = functools.partial(
                loop.run_in_executor, None, self.event_handler.emit
            )
            asyncio.create_task(self.process_input_frames())
            asyncio.create_task(
                player_worker_decode(
                    callable,
                    self.queue,
                    self.thread_quit,
                    False,
                    self.event_handler.output_sample_rate,
                    self.event_handler.output_frame_size,
                )
            )
            self.has_started = True

    async def recv(self):
        try:
            if self.readyState != "live":
                raise MediaStreamError

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
                self._start = time.time() - data_time
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


class ServerToClientVideo(VideoStreamTrack):
    """
    This works for streaming input and output
    """

    kind = "video"

    def __init__(
        self,
        event_handler: Callable,
    ) -> None:
        super().__init__()  # don't forget this!
        self.event_handler = event_handler
        self.args_set = asyncio.Event()
        self.latest_args: str | list[Any] = "not_set"
        self.generator: Generator[Any, None, Any] | None = None

    def array_to_frame(self, array: np.ndarray) -> VideoFrame:
        return VideoFrame.from_ndarray(array, format="bgr24")

    async def recv(self):
        try:
            pts, time_base = await self.next_timestamp()
            await self.args_set.wait()
            if self.generator is None:
                self.generator = cast(
                    Generator[Any, None, Any], self.event_handler(*self.latest_args)
                )

            try:
                next_array = next(self.generator)
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
    ) -> None:
        self.generator: Generator[Any, None, Any] | None = None
        self.event_handler = event_handler
        self.current_timestamp = 0
        self.latest_args: str | list[Any] = "not_set"
        self.args_set = threading.Event()
        self.queue = asyncio.Queue()
        self.thread_quit = asyncio.Event()
        self.has_started = False
        self._start: float | None = None
        super().__init__()

    def next(self) -> tuple[int, np.ndarray] | None:
        self.args_set.wait()
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
                    True,
                )
            )
            self.has_started = True

    async def recv(self):
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
                    self._start = time.time() - data_time
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
        str, VideoCallback | ServerToClientVideo | ServerToClientAudio | AudioCallback
    ] = {}

    EVENTS = ["tick"]

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
        mode: Literal["send-receive", "receive"] = "send-receive",
        modality: Literal["video", "audio"] = "video",
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
            include_audio: whether the component should record/retain the audio track for a video. By default, audio is excluded for webcam videos and included for uploaded videos.
            autoplay: whether to automatically play the video when the component is used as an output. Note: browsers will not autoplay video files if the user has not interacted with the page yet.
            show_share_button: if True, will show a share icon in the corner of the component that allows user to share outputs to Hugging Face Spaces Discussions. If False, icon does not appear. If set to None (default behavior), then the icon appears if this Gradio app is launched on Spaces, but not otherwise.
            show_download_button: if True, will show a download icon in the corner of the component that allows user to download the output. If False, icon does not appear. By default, it will be True for output components and False for input components.
            min_length: the minimum length of video (in seconds) that the user can pass into the prediction function. If None, there is no minimum length.
            max_length: the maximum length of video (in seconds) that the user can pass into the prediction function. If None, there is no maximum length.
            loop: if True, the video will loop when it reaches the end and continue playing from the beginning.
            streaming: when used set as an output, takes video chunks yielded from the backend and combines them into one streaming video output. Each chunk should be a video file with a .ts extension using an h.264 encoding. Mp4 files are also accepted but they will be converted to h.264 encoding.
            watermark: an image file to be included as a watermark on the video. The image is not scaled and is displayed on the bottom right of the video. Valid formats for the image are: jpeg, png.
        """
        self.time_limit = time_limit
        self.height = height
        self.width = width
        self.mirror_webcam = mirror_webcam
        self.concurrency_limit = 1
        self.rtc_configuration = rtc_configuration
        self.mode = mode
        self.modality = modality
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

    def set_output(self, webrtc_id: str, *args):
        if webrtc_id in self.connections:
            if self.mode == "send-receive":
                self.connections[webrtc_id].latest_args = ["__webrtc_value__"] + list(
                    args
                )
            elif self.mode == "receive":
                self.connections[webrtc_id].latest_args = list(args)
                self.connections[webrtc_id].args_set.set()  # type: ignore

    def stream(
        self,
        fn: Callable[..., Any] | StreamHandler | None = None,
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
        self.event_handler = fn
        self.time_limit = time_limit

        if (
            self.mode == "send-receive"
            and self.modality == "audio"
            and not isinstance(self.event_handler, StreamHandler)
        ):
            raise ValueError(
                "In the send-receive mode for audio, the event handler must be an instance of StreamHandler."
            )

        if self.mode == "send-receive":
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
            return self.tick(  # type: ignore
                self.set_output,
                inputs=inputs,
                outputs=None,
                concurrency_id=concurrency_id,
                concurrency_limit=None,
                stream_every=0.5,
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
                self.set_output,
                inputs=[self] + list(inputs),
                outputs=None,
                concurrency_id=concurrency_id,
            )

    @staticmethod
    async def wait_for_time_limit(pc: RTCPeerConnection, time_limit: float):
        await asyncio.sleep(time_limit)
        await pc.close()

    @server
    async def offer(self, body):
        logger.debug("Starting to handle offer")
        logger.debug("Offer body %s", body)
        if len(self.connections) >= cast(int, self.concurrency_limit):
            return {"status": "failed"}

        offer = RTCSessionDescription(sdp=body["sdp"], type=body["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

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
                connection = self.connections.pop(body["webrtc_id"], None)
                if connection:
                    connection.stop()
                self.pcs.discard(pc)
            if pc.connectionState == "connected":
                if self.time_limit is not None:
                    asyncio.create_task(self.wait_for_time_limit(pc, self.time_limit))

        @pc.on("track")
        def on_track(track):
            relay = MediaRelay()
            if self.modality == "video":
                cb = VideoCallback(
                    relay.subscribe(track),
                    event_handler=cast(Callable, self.event_handler),
                )
            elif self.modality == "audio":
                cb = AudioCallback(
                    relay.subscribe(track),
                    event_handler=cast(StreamHandler, self.event_handler).copy(),
                )
            self.connections[body["webrtc_id"]] = cb
            logger.debug("Adding track to peer connection %s", cb)
            pc.addTrack(cb)

        if self.mode == "receive":
            if self.modality == "video":
                cb = ServerToClientVideo(cast(Callable, self.event_handler))
            elif self.modality == "audio":
                cb = ServerToClientAudio(cast(Callable, self.event_handler))

            logger.debug("Adding track to peer connection %s", cb)
            pc.addTrack(cb)
            self.connections[body["webrtc_id"]] = cb
            cb.on("ended", lambda: self.connections.pop(body["webrtc_id"], None))

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)  # type: ignore
        logger.debug("done handling offer about to return")

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
