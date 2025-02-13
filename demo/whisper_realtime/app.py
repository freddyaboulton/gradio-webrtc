from pathlib import Path

import gradio as gr
from gradio.utils import get_space
import numpy as np
import json
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, StreamingResponse
from fastrtc import (
    AdditionalOutputs,
    ReplyOnPause,
    Stream,
    audio_to_bytes,
    get_twilio_turn_credentials,
)
from groq import AsyncClient

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
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
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
    rtc_config = get_twilio_turn_credentials() if get_space() else None
    html_content = (cur_dir / "index.html").read_text()
    html_content = html_content.replace("__RTC_CONFIGURATION__", json.dumps(rtc_config))
    return HTMLResponse(content=open(cur_dir / "index.html").read())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(stream, host="0.0.0.0", port=7860)
