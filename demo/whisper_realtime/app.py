from fastapi.responses import StreamingResponse, HTMLResponse
import gradio as gr
import numpy as np
from groq import AsyncClient
from fastrtc import (
    Stream,
    AdditionalOutputs,
    ReplyOnPause,
    audio_to_bytes,
)
from pathlib import Path
from dotenv import load_dotenv

cur_dir = Path(__file__).parent

load_dotenv()


groq_client = AsyncClient()


async def transcribe(audio: tuple[int, np.ndarray]):
    transcript = await groq_client.audio.transcriptions.create(
        file=("audio-file.mp3", audio_to_bytes(audio)),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
    )
    yield AdditionalOutputs(transcript.text)


stream = Stream(
    ReplyOnPause(transcribe),
    modality="audio",
    mode="send",
    additional_outputs=[
        gr.Textbox(label="Transcript"),
    ],
    additional_outputs_handler=lambda a, b: a + " " + b,
)


@stream.get("/transcript")
def _(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            transcript = output.args[0]
            yield f"event: output\ndata: {transcript}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")


@stream.get("/")
def index():
    return HTMLResponse(content=open(cur_dir / "index.html").read())
