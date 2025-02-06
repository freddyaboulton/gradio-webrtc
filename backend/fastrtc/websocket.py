import asyncio
import audioop
import base64
import logging
from typing import Optional

import librosa
import numpy as np
from fastapi import WebSocket

from .tracks import AsyncStreamHandler, StreamHandlerImpl
from .utils import split_output

logger = logging.getLogger(__file__)


def convert_to_mulaw(audio_data: np.ndarray, original_rate: int) -> bytes:
    """Convert audio data to 8kHz mu-law format"""

    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32768.0

    if original_rate != 8000:
        audio_data = librosa.resample(audio_data, orig_sr=original_rate, target_sr=8000)

    audio_data = (audio_data * 32768).astype(np.int16)

    return audioop.lin2ulaw(audio_data, 2)  # type: ignore


class WebSocketHandler:
    def __init__(self, stream_handler: StreamHandlerImpl):
        self.stream_handler = stream_handler
        self.websocket: Optional[WebSocket] = None
        self._emit_task: Optional[asyncio.Task] = None
        self.stream_sid: Optional[str] = None

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket
        self._emit_task = asyncio.create_task(self._emit_loop())

        try:
            while True:
                message = await websocket.receive_json()

                if message["event"] == "media":
                    audio_payload = base64.b64decode(message["media"]["payload"])

                    audio_array = np.frombuffer(
                        audioop.ulaw2lin(audio_payload, 2), dtype=np.int16
                    )

                    if isinstance(self.stream_handler, AsyncStreamHandler):
                        await self.stream_handler.receive((8000, audio_array))
                    else:
                        self.stream_handler.receive((8000, audio_array))

                elif message["event"] == "start":
                    self.stream_sid = message["streamSid"]

                elif message["event"] == "stop":
                    break

        except Exception as e:
            logger.debug("Error in websocket handler %s", e)
        finally:
            if self._emit_task:
                self._emit_task.cancel()
            await websocket.close()

    async def _emit_loop(self):
        try:
            while True:
                if isinstance(self.stream_handler, AsyncStreamHandler):
                    output = await self.stream_handler.emit()
                else:
                    output = self.stream_handler.emit()

                if output is not None:
                    frame, _ = split_output(output)
                    if not isinstance(frame, tuple):
                        continue

                    mulaw_audio = convert_to_mulaw(frame[1], frame[0])
                    audio_payload = base64.b64encode(mulaw_audio).decode("utf-8")

                    if self.websocket and self.stream_sid:
                        await self.websocket.send_json(
                            {
                                "event": "media",
                                "media": {"payload": audio_payload},
                                "streamSid": self.stream_sid,
                            }
                        )

                await asyncio.sleep(0.02)

        except asyncio.CancelledError:
            logger.debug("Emit loop cancelled")
        except Exception as e:
            logger.debug("Error in emit loop: %s", e)
