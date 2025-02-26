import base64
import json
import os
from pathlib import Path

import gradio as gr
import huggingface_hub
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastrtc import (
    AdditionalOutputs,
    ReplyOnStopWords,
    Stream,
    get_stt_model,
    get_twilio_turn_credentials,
)
from gradio.utils import get_space
from pydantic import BaseModel

load_dotenv()

curr_dir = Path(__file__).parent


client = huggingface_hub.InferenceClient(
    api_key=os.environ.get("SAMBANOVA_API_KEY"),
    provider="sambanova",
)
model = get_stt_model()


def response(
    audio: tuple[int, np.ndarray],
    gradio_chatbot: list[dict] | None = None,
    conversation_state: list[dict] | None = None,
):
    gradio_chatbot = gradio_chatbot or []
    conversation_state = conversation_state or []
    text = model.stt(audio)
    print("STT in handler", text)
    sample_rate, array = audio
    gradio_chatbot.append(
        {"role": "user", "content": gr.Audio((sample_rate, array.squeeze()))}
    )
    yield AdditionalOutputs(gradio_chatbot, conversation_state)

    conversation_state.append({"role": "user", "content": text})

    request = client.chat.completions.create(
        model="meta-llama/Llama-3.2-3B-Instruct",
        messages=conversation_state,  # type: ignore
        temperature=0.1,
        top_p=0.1,
    )
    response = {"role": "assistant", "content": request.choices[0].message.content}

    conversation_state.append(response)
    gradio_chatbot.append(response)

    yield AdditionalOutputs(gradio_chatbot, conversation_state)


chatbot = gr.Chatbot(type="messages", value=[])
state = gr.State(value=[])
stream = Stream(
    ReplyOnStopWords(
        response,  # type: ignore
        stop_words=["computer"],
        input_sample_rate=16000,
    ),
    mode="send",
    modality="audio",
    additional_inputs=[chatbot, state],
    additional_outputs=[chatbot, state],
    additional_outputs_handler=lambda *a: (a[2], a[3]),
    concurrency_limit=5 if get_space() else None,
    time_limit=90 if get_space() else None,
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
)
app = FastAPI()
stream.mount(app)


class Message(BaseModel):
    role: str
    content: str


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[Message]
    state: list[Message]


@app.get("/")
async def _():
    rtc_config = get_twilio_turn_credentials() if get_space() else None
    html_content = (curr_dir / "index.html").read_text()
    html_content = html_content.replace("__RTC_CONFIGURATION__", json.dumps(rtc_config))
    return HTMLResponse(content=html_content)


@app.post("/input_hook")
async def _(data: InputData):
    body = data.model_dump()
    stream.set_input(data.webrtc_id, body["chatbot"], body["state"])


def audio_to_base64(file_path):
    audio_format = "wav"
    with open(file_path, "rb") as audio_file:
        encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")
    return f"data:audio/{audio_format};base64,{encoded_audio}"


@app.get("/outputs")
async def _(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            chatbot = output.args[0]
            state = output.args[1]
            data = {
                "message": state[-1],
                "audio": audio_to_base64(chatbot[-1]["content"].value["path"])
                if chatbot[-1]["role"] == "user"
                else None,
            }
            yield f"event: output\ndata: {json.dumps(data)}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import os

    if (mode := os.getenv("MODE")) == "UI":
        stream.ui.launch(server_port=7860)
    elif mode == "PHONE":
        raise ValueError("Phone mode not supported")
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=7860)
