import asyncio
import base64
import io
from typing import Optional

import numpy as np
from fastapi import WebSocket
from pydub import AudioSegment

from .tracks import AsyncStreamHandler, StreamHandlerImpl


def convert_to_mulaw(audio_data: np.ndarray, original_rate: int) -> bytes:
    """Convert audio data to 8kHz mu-law format"""
    # Create AudioSegment from numpy array
    # Assuming audio_data is int16. If float32, we need to convert to int16 first
    if audio_data.dtype == np.float32:
        audio_data = (audio_data * 32768).astype(np.int16)

    # Create AudioSegment
    audio_segment = AudioSegment(
        audio_data.tobytes(),
        frame_rate=original_rate,
        sample_width=2,  # 16-bit
        channels=1,  # mono
    )

    # Convert to 8kHz
    if original_rate != 8000:
        audio_segment = audio_segment.set_frame_rate(8000)

    # Export as mu-law
    buf = io.BytesIO()
    audio_segment.export(buf, format="raw", codec="mulaw")
    return buf.getvalue()


class WebSocketHandler:
    def __init__(self, stream_handler: StreamHandlerImpl):
        self.stream_handler = stream_handler
        self.websocket: Optional[WebSocket] = None
        self._emit_task: Optional[asyncio.Task] = None
        self.stream_sid: Optional[str] = None

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket

        # Start emitting task
        self._emit_task = asyncio.create_task(self._emit_loop())

        try:
            while True:
                message = await websocket.receive_json()

                if message["event"] == "media":
                    # Decode base64 audio payload
                    audio_payload = base64.b64decode(message["media"]["payload"])

                    # Convert to numpy array (assuming 16-bit PCM)
                    audio_array = np.frombuffer(audio_payload, dtype=np.int16)

                    # Pass to stream handler
                    if isinstance(self.stream_handler, AsyncStreamHandler):
                        await self.stream_handler.receive(
                            (self.stream_handler.input_sample_rate, audio_array)
                        )
                    else:
                        self.stream_handler.receive(
                            (self.stream_handler.input_sample_rate, audio_array)
                        )

                elif message["event"] == "start":
                    # Store the StreamSid from the start event
                    self.stream_sid = message["streamSid"]

                elif message["event"] == "stop":
                    # Handle stream stop event
                    break

        except Exception as e:
            print(f"Error in websocket handler: {e}")
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
                    # Handle different output types
                    if isinstance(output, tuple):
                        if len(output) == 2 and isinstance(output[1], np.ndarray):
                            sample_rate, audio_data = output
                        else:
                            # Handle AdditionalOutputs case
                            (sample_rate, audio_data), _ = output

                    # Convert to 8kHz mu-law format
                    mulaw_audio = convert_to_mulaw(audio_data, sample_rate)

                    # Convert to base64
                    audio_payload = base64.b64encode(mulaw_audio).decode("utf-8")

                    # Send media message
                    if self.websocket and self.stream_sid:
                        await self.websocket.send_json(
                            {
                                "event": "media",
                                "media": {"payload": audio_payload},
                                "streamSid": self.stream_sid,
                            }
                        )

                # Add a small delay to prevent tight loop
                await asyncio.sleep(0.02)  # 20ms delay

        except asyncio.CancelledError:
            print("Emit loop cancelled")
        except Exception as e:
            print(f"Error in emit loop: {e}")
