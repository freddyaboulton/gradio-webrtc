"""gr.Video() component."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, cast


from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from aiortc import VideoStreamTrack
from aiortc.mediastreams import MediaStreamError
from aiortc.contrib.media import VideoFrame # type: ignore
from gradio_client import handle_file
import numpy as np


from gradio import utils, wasm_utils
from gradio.components.base import Component, server

if TYPE_CHECKING:
    from gradio.components import Timer
    from gradio.blocks import Block


if wasm_utils.IS_WASM:
    raise ValueError("Not supported in gradio-lite!")



class VideoCallback(VideoStreamTrack):
    """
    This works for streaming input and output
    """

    kind = "video"

    def __init__(
        self,
        track,
        event_handler: Callable,
    ) -> None:
        super().__init__()  # don't forget this!
        self.track = track
        self.event_handler = event_handler
        self.latest_args: str | list[Any] = "not_set"

    def add_frame_to_payload(self, args: list[Any], frame: np.ndarray | None) -> list[Any]:
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
                frame = await self.track.recv()
            except MediaStreamError:
                return
            frame_array = frame.to_ndarray(format="bgr24")

            if self.latest_args == "not_set":
                print("args not set")
                return frame
            

            args = self.add_frame_to_payload(self.latest_args, frame_array)
            
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
            print(e)
            import traceback

            traceback.print_exc()


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
    connections: dict[str, VideoCallback] = {}

    EVENTS = [
        "tick"
    ]

    def __init__(
        self,
        value: str
        | Path
        | tuple[str | Path, str | Path | None]
        | Callable
        | None = None,
        *,
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
        show_share_button: bool | None = None,
        show_download_button: bool | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        streaming: bool = False,
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
        self.height = height
        self.width = width
        self.mirror_webcam = mirror_webcam
        self.concurrency_limit = 1
        self.show_share_button = (
            (utils.get_space() is not None)
            if show_share_button is None
            else show_share_button
        )
        self.show_download_button = show_download_button
        self.min_length = min_length
        self.max_length = max_length
        self.streaming = streaming
        self.event_handler: Callable | None = None
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
        return "__webrtc_value__"

    def set_output(self, webrtc_id: str, *args):
        if webrtc_id in self.connections:
            self.connections[webrtc_id].latest_args = ["__webrtc_value__"] + list(args)
    
    def webrtc_stream(
        self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        js: str | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        stream_every: float = 0.5,
        time_limit: float | None = None):

        if inputs[0] != self:
            raise ValueError("In the webrtc_stream event, the first input component must be the WebRTC component.")
    
        self.concurrency_limit = 1 if concurrency_limit in ["default", None] else concurrency_limit
        self.event_handler = fn
        return self.tick(self.set_output,
                    inputs=inputs,
                    outputs=None,
                    concurrency_id=concurrency_id,
                    concurrency_limit=None,
                    stream_every=stream_every,
                    time_limit=None,
                    js=js
                    )

    @server
    async def offer(self, body):

        if len(self.connections) >= self.concurrency_limit:
            return {"status": "failed"}

        
        offer = RTCSessionDescription(sdp=body['sdp'], type=body['type'])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print(pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                self.connections.pop(body['webrtc_id'], None)
                self.pcs.discard(pc)

        @pc.on("track")
        def on_track(track):
            cb = VideoCallback(
                    self.relay.subscribe(track),
                    event_handler=cast(Callable, self.event_handler)
                )
            self.connections[body['webrtc_id']] = cb
            pc.addTrack(cb)
       
        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)  # type: ignore

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
