import asyncio
import audioop
import base64
import logging
from typing import Any, Awaitable, Callable, Optional, cast

import anyio
import librosa
import numpy as np
from fastapi import WebSocket

from .tracks import AsyncStreamHandler, StreamHandlerImpl
from .utils import AdditionalOutputs, DataChannel, split_output


class WebSocketDataChannel(DataChannel):
    def __init__(self, websocket: WebSocket, loop: asyncio.AbstractEventLoop):
        self.websocket = websocket
        self.loop = loop

    def send(self, message: str) -> None:
        asyncio.run_coroutine_threadsafe(self.websocket.send_text(message), self.loop)


logger = logging.getLogger(__file__)


def convert_to_mulaw(
    audio_data: np.ndarray, original_rate: int, target_rate: int
) -> bytes:
    """Convert audio data to 8kHz mu-law format"""

    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32768.0

    if original_rate != target_rate:
        audio_data = librosa.resample(audio_data, orig_sr=original_rate, target_sr=8000)

    audio_data = (audio_data * 32768).astype(np.int16)

    return audioop.lin2ulaw(audio_data, 2)  # type: ignore


run_sync = anyio.to_thread.run_sync  # type: ignore


class WebSocketHandler:
    def __init__(
        self,
        stream_handler: StreamHandlerImpl,
        set_handler: Callable[[str, "WebSocketHandler"], Awaitable[None]],
        clean_up: Callable[[str], None],
        additional_outputs_factory: Callable[
            [str], Callable[[AdditionalOutputs], None]
        ],
    ):
        self.stream_handler = stream_handler
        self.websocket: Optional[WebSocket] = None
        self._emit_task: Optional[asyncio.Task] = None
        self.stream_id: Optional[str] = None
        self.set_additional_outputs_factory = additional_outputs_factory
        self.set_additional_outputs: Callable[[AdditionalOutputs], None]
        self.set_handler = set_handler
        self.quit = asyncio.Event()
        self.clean_up = clean_up

    def set_args(self, args: list[Any]):
        self.stream_handler.set_args(args)

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        loop = asyncio.get_running_loop()
        self.loop = loop
        self.websocket = websocket
        self.data_channel = WebSocketDataChannel(websocket, loop)
        self.stream_handler._loop = loop
        self.stream_handler.set_channel(self.data_channel)
        self._emit_task = asyncio.create_task(self._emit_loop())
        if isinstance(self.stream_handler, AsyncStreamHandler):
            start_up = self.stream_handler.start_up()
        else:
            start_up = anyio.to_thread.run_sync(self.stream_handler.start_up)  # type: ignore

        self.start_up_task = asyncio.create_task(start_up)
        try:
            while not self.quit.is_set():
                message = await websocket.receive_json()

                if message["event"] == "media":
                    audio_payload = base64.b64decode(message["media"]["payload"])

                    audio_array = np.frombuffer(
                        audioop.ulaw2lin(audio_payload, 2), dtype=np.int16
                    )

                    if self.stream_handler.input_sample_rate != 8000:
                        audio_array = audio_array.astype(np.float32) / 32768.0
                        audio_array = librosa.resample(
                            audio_array,
                            orig_sr=8000,
                            target_sr=self.stream_handler.input_sample_rate,
                        )
                        audio_array = (audio_array * 32768).astype(np.int16)
                    if isinstance(self.stream_handler, AsyncStreamHandler):
                        await self.stream_handler.receive(
                            (self.stream_handler.input_sample_rate, audio_array)
                        )
                    else:
                        await run_sync(
                            self.stream_handler.receive,
                            (self.stream_handler.input_sample_rate, audio_array),
                        )

                elif message["event"] == "start":
                    if self.stream_handler.phone_mode:
                        self.stream_id = cast(str, message["streamSid"])
                    else:
                        self.stream_id = cast(str, message["websocket_id"])
                    self.set_additional_outputs = self.set_additional_outputs_factory(
                        self.stream_id
                    )
                    await self.set_handler(self.stream_id, self)
                elif message["event"] == "stop":
                    self.quit.set()
                    self.clean_up(cast(str, self.stream_id))
                    return
                elif message["event"] == "ping":
                    await websocket.send_json({"event": "pong"})

        except Exception as e:
            print(e)
            import traceback

            traceback.print_exc()
            logger.debug("Error in websocket handler %s", e)
        finally:
            if self._emit_task:
                self._emit_task.cancel()
            if self.start_up_task:
                self.start_up_task.cancel()
            await websocket.close()

    async def _emit_loop(self):
        try:
            while not self.quit.is_set():
                if isinstance(self.stream_handler, AsyncStreamHandler):
                    output = await self.stream_handler.emit()
                else:
                    output = await run_sync(self.stream_handler.emit)

                if output is not None:
                    frame, output = split_output(output)
                    if output is not None:
                        self.set_additional_outputs(output)
                    if not isinstance(frame, tuple):
                        continue
                    target_rate = (
                        self.stream_handler.output_sample_rate
                        if not self.stream_handler.phone_mode
                        else 8000
                    )
                    mulaw_audio = convert_to_mulaw(
                        frame[1], frame[0], target_rate=target_rate
                    )
                    audio_payload = base64.b64encode(mulaw_audio).decode("utf-8")

                    if self.websocket and self.stream_id:
                        payload = {
                            "event": "media",
                            "media": {"payload": audio_payload},
                        }
                        if self.stream_handler.phone_mode:
                            payload["streamSid"] = self.stream_id
                        await self.websocket.send_json(payload)

                await asyncio.sleep(0.02)

        except asyncio.CancelledError:
            logger.debug("Emit loop cancelled")
        except Exception as e:
            import traceback

            traceback.print_exc()
            logger.debug("Error in emit loop: %s", e)
