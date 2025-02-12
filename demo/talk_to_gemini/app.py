import asyncio
import base64
import pathlib
from typing import AsyncGenerator, Literal
from dotenv import load_dotenv
import os
from google import genai
from pydantic import BaseModel
from google.genai.types import (
    LiveConnectConfig,
    PrebuiltVoiceConfig,
    SpeechConfig,
    VoiceConfig,
)
import gradio as gr
from fastrtc import Stream, AsyncStreamHandler, async_aggregate_bytes_to_16bit
import numpy as np
from fastapi.responses import HTMLResponse

current_dir = pathlib.Path(__file__).parent

load_dotenv()


def encode_audio(data: np.ndarray) -> str:
    """Encode Audio data to send to the server"""
    return base64.b64encode(data.tobytes()).decode("UTF-8")


class GeminiHandler(AsyncStreamHandler):
    """Handler for the Gemini API"""

    def __init__(
        self,
        expected_layout: Literal["mono"] = "mono",
        output_sample_rate: int = 24000,
        output_frame_size: int = 480,
    ) -> None:
        super().__init__(
            expected_layout,
            output_sample_rate,
            output_frame_size,
            input_sample_rate=16000,
        )
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()

    def copy(self) -> "GeminiHandler":
        """Required implementation of the copy method for AsyncStreamHandler"""
        return GeminiHandler(
            expected_layout="mono",
            output_sample_rate=self.output_sample_rate,
            output_frame_size=self.output_frame_size,
        )

    async def stream(self) -> AsyncGenerator[bytes, None]:
        """Helper method to stream input audio to the server. Used in start_stream."""
        while not self.quit.is_set():
            audio = await self.input_queue.get()
            yield audio
        return

    async def connect(
        self, api_key: str | None = None, voice_name: str | None = None
    ) -> AsyncGenerator[bytes, None]:
        """Connect to to genai server and start the stream"""
        print("Connecting to Gemini", api_key, voice_name)
        client = genai.Client(
            api_key=api_key or os.getenv("GEMINI_API_KEY"),
            http_options={"api_version": "v1alpha"},
        )
        config = LiveConnectConfig(
            response_modalities=["AUDIO"],  # type: ignore
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        )
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp", config=config
        ) as session:
            async for audio in session.start_stream(
                stream=self.stream(), mime_type="audio/pcm"
            ):
                if audio.data:
                    yield audio.data

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        """Receive audio from the user and put it in the input stream."""
        _, array = frame
        array = array.squeeze()
        audio_message = encode_audio(array)
        self.input_queue.put_nowait(audio_message)

    async def generator(self) -> None:
        """Helper method for placing audio from the server into the output queue."""
        async for audio_response in async_aggregate_bytes_to_16bit(
            self.connect(*self.latest_args[1:])
        ):
            self.output_queue.put_nowait(audio_response)

    async def emit(self) -> tuple[int, np.ndarray]:
        """Required implementation of the emit method for AsyncStreamHandler"""
        if not self.args_set.is_set():
            if not self.phone_mode:
                await self.wait_for_args()
            else:
                self.args_set.set()
            asyncio.create_task(self.generator())

        array = await self.output_queue.get()
        return (self.output_sample_rate, array)

    def shutdown(self) -> None:
        """Stop the stream method on shutdown"""
        self.quit.set()
        self.args_set.clear()
        self.quit.clear()


stream = Stream(
    modality="audio",
    mode="send-receive",
    handler=GeminiHandler(),
    additional_inputs=[
        gr.Textbox(label="API Key", type="password", value=os.getenv("GEMINI_API_KEY")),
        gr.Dropdown(
            label="Voice",
            choices=[
                "Puck",
                "Charon",
                "Kore",
                "Fenrir",
                "Aoede",
            ],
            value="Puck",
        ),
    ],
)


class InputData(BaseModel):
    webrtc_id: str
    voice_name: str
    api_key: str


@stream.post("/input_hook")
async def _(body: InputData):
    stream.set_input(body.webrtc_id, body.api_key, body.voice_name)
    return {"status": "ok"}


@stream.get("/")
async def index():
    return HTMLResponse(
        content=(current_dir / "index.html").read_text(), status_code=200
    )
