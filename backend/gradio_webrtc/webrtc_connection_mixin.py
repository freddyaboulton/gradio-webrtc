"""Mixin for handling WebRTC connections."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import (
    Literal,
    ParamSpec,
    TypeVar,
    cast,
)

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaRelay  # type: ignore

from gradio_webrtc.tracks import (
    AudioCallback,
    ServerToClientAudio,
    ServerToClientVideo,
    StreamHandlerBase,
    StreamHandlerImpl,
    VideoCallback,
    VideoStreamHandler,
)
from gradio_webrtc.utils import (
    AdditionalOutputs,
    DataChannel,
    create_message,
)

Track = (
    VideoCallback
    | VideoStreamHandler
    | AudioCallback
    | ServerToClientAudio
    | ServerToClientVideo
)

logger = logging.getLogger(__name__)


# For the return type
R = TypeVar("R")
# For the parameter specification
P = ParamSpec("P")


class WebRTCConnectionMixin:
    pcs: set[RTCPeerConnection] = set([])
    relay = MediaRelay()
    connections: dict[str, list[Track]] = defaultdict(list)
    data_channels: dict[str, DataChannel] = {}
    additional_outputs: dict[str, list[AdditionalOutputs]] = {}
    handlers: dict[str, StreamHandlerBase | Callable] = {}

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

    def set_input(self, webrtc_id: str, *args):
        if webrtc_id in self.connections:
            for conn in self.connections[webrtc_id]:
                conn.set_args(list(args))

    def get_output(self, webrtc_id: str) -> list[AdditionalOutputs]:
        return self.additional_outputs.get(webrtc_id, [])

    def set_additional_outputs(
        self, webrtc_id: str
    ) -> Callable[[AdditionalOutputs], None]:
        def set_outputs(outputs: AdditionalOutputs):
            if webrtc_id not in self.additional_outputs:
                self.additional_outputs[webrtc_id] = []
            self.additional_outputs[webrtc_id].append(outputs)

        return set_outputs

    async def handle_offer(self, body, set_outputs):
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

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.debug("ICE connection state change %s", pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.connections.pop(body["webrtc_id"], None)
                self.pcs.discard(pc)

        @pc.on("connectionstatechange")
        async def _():
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
        def _(track):
            relay = MediaRelay()
            handler = self.handlers[body["webrtc_id"]]

            if self.modality == "video" and track.kind == "video":
                cb = VideoCallback(
                    relay.subscribe(track),
                    event_handler=cast(Callable, handler),
                    set_additional_outputs=set_outputs,
                    mode=cast(Literal["send", "send-receive"], self.mode),
                )
            elif self.modality == "audio-video" and track.kind == "video":
                cb = VideoStreamHandler(
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
        def _(channel):
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
            def _(message):
                logger.debug(f"Received message: {message}")
                if channel.readyState == "open":
                    channel.send(
                        create_message("log", data=f"Server received: {message}")
                    )

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
