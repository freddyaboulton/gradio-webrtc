import json
import logging
import os
from pathlib import Path

import anthropic
import gradio as gr
import numpy as np
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from fastapi.responses import HTMLResponse, StreamingResponse
from fastrtc import AdditionalOutputs, ReplyOnPause, Stream, get_twilio_turn_credentials
from fastrtc.utils import aggregate_bytes_to_16bit, audio_to_bytes
from gradio.utils import get_space
from groq import Groq
from pydantic import BaseModel

# Configure the root logger to WARNING to suppress debug messages from other libraries
logging.basicConfig(level=logging.WARNING)

# Create a console handler
console_handler = logging.FileHandler("gradio_webrtc.log")
console_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Configure the logger for your specific library
logger = logging.getLogger("fastrtc")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)


load_dotenv()

groq_client = Groq()
claude_client = anthropic.Anthropic()
tts_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

curr_dir = Path(__file__).parent


def response(
    audio: tuple[int, np.ndarray],
    chatbot: list[dict] | None = None,
):
    chatbot = chatbot or []
    messages = [{"role": d["role"], "content": d["content"]} for d in chatbot]
    prompt = groq_client.audio.transcriptions.create(
        file=("audio-file.mp3", audio_to_bytes(audio)),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
    ).text
    print("prompt", prompt)
    chatbot.append({"role": "user", "content": prompt})
    messages.append({"role": "user", "content": prompt})
    response = claude_client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=512,
        messages=messages,  # type: ignore
    )
    response_text = " ".join(
        block.text  # type: ignore
        for block in response.content
        if getattr(block, "type", None) == "text"
    )
    chatbot.append({"role": "assistant", "content": response_text})
    yield AdditionalOutputs(chatbot)
    iterator = tts_client.text_to_speech.convert_as_stream(
        text=response_text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="pcm_24000",
    )
    for chunk in aggregate_bytes_to_16bit(iterator):
        audio_array = np.frombuffer(chunk, dtype=np.int16).reshape(1, -1)
        yield (24000, audio_array, "mono")


chatbot = gr.Chatbot(type="messages")
stream = Stream(
    modality="audio",
    mode="send-receive",
    handler=ReplyOnPause(response),
    additional_outputs_handler=lambda a, b: b,
    additional_inputs=[chatbot],
    additional_outputs=[chatbot],
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
    concurrency_limit=20 if get_space() else None,
)


class Message(BaseModel):
    role: str
    content: str


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[Message]


@stream.get("/")
async def _():
    rtc_config = get_twilio_turn_credentials() if get_space() else None
    html_content = (curr_dir / "index.html").read_text()
    html_content = html_content.replace("__RTC_CONFIGURATION__", json.dumps(rtc_config))
    return HTMLResponse(content=html_content, status_code=200)


@stream.post("/input_hook")
async def _(body: InputData):
    stream.set_input(body.webrtc_id, body.model_dump()["chatbot"])
    return {"status": "ok"}


@stream.get("/outputs")
def _(webrtc_id: str):
    print("outputs", webrtc_id)

    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            chatbot = output.args[0]
            yield f"event: output\ndata: {json.dumps(chatbot[-2])}\n\n"
            yield f"event: output\ndata: {json.dumps(chatbot[-1])}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    s = uvicorn.run(stream, port=7860, host="0.0.0.0")
