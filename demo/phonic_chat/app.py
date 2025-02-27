import asyncio
import base64
import os

import gradio as gr
from gradio.utils import get_space
import numpy as np
from dotenv import load_dotenv
from fastrtc import (
    AdditionalOutputs,
    AsyncStreamHandler,
    Stream,
    get_twilio_turn_credentials,
    audio_to_float32,
    wait_for_item,
)
from phonic.client import PhonicSTSClient, get_voices

load_dotenv()

STS_URI = "wss://api.phonic.co/v1/sts/ws"
API_KEY = os.environ["PHONIC_API_KEY"]
SAMPLE_RATE = 44_100
voices = get_voices(API_KEY)
voice_ids = [voice["id"] for voice in voices]


class PhonicHandler(AsyncStreamHandler):
    def __init__(self):
        super().__init__(input_sample_rate=SAMPLE_RATE, output_sample_rate=SAMPLE_RATE)
        self.output_queue = asyncio.Queue()
        self.client = None

    def copy(self) -> AsyncStreamHandler:
        return PhonicHandler()

    async def start_up(self):
        await self.wait_for_args()
        voice_id = self.latest_args[1]
        async with PhonicSTSClient(STS_URI, API_KEY) as client:
            self.client = client
            sts_stream = client.sts(  # type: ignore
                input_format="pcm_44100",
                output_format="pcm_44100",
                system_prompt="You are a helpful voice assistant. Respond conversationally.",
                # welcome_message="Hello! I'm your voice assistant. How can I help you today?",
                voice_id=voice_id,
            )
            async for message in sts_stream:
                message_type = message.get("type")
                if message_type == "audio_chunk":
                    audio_b64 = message["audio"]
                    audio_bytes = base64.b64decode(audio_b64)
                    await self.output_queue.put(
                        (SAMPLE_RATE, np.frombuffer(audio_bytes, dtype=np.int16))
                    )
                    if text := message.get("text"):
                        msg = {"role": "assistant", "content": text}
                        await self.output_queue.put(AdditionalOutputs(msg))
                elif message_type == "input_text":
                    msg = {"role": "user", "content": message["text"]}
                    await self.output_queue.put(AdditionalOutputs(msg))

    async def emit(self):
        return await wait_for_item(self.output_queue)

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        if not self.client:
            return
        audio_float32 = audio_to_float32(frame)
        await self.client.send_audio(audio_float32)  # type: ignore

    async def shutdown(self):
        if self.client:
            await self.client._websocket.close()
        return super().shutdown()


def add_to_chatbot(chatbot, message):
    chatbot.append(message)
    return chatbot


chatbot = gr.Chatbot(type="messages", value=[])
stream = Stream(
    handler=PhonicHandler(),
    mode="send-receive",
    modality="audio",
    additional_inputs=[
        gr.Dropdown(
            choices=voice_ids,
            value="victoria",
            label="Voice",
            info="Select a voice from the dropdown",
        )
    ],
    additional_outputs=[chatbot],
    additional_outputs_handler=add_to_chatbot,
    ui_args={
        "title": "Phonic Chat (Powered by FastRTC ⚡️)",
    },
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
    concurrency_limit=5 if get_space() else None,
    time_limit=90 if get_space() else None,
)

# with stream.ui:
#     state.change(lambda s: s, inputs=state, outputs=chatbot)

if __name__ == "__main__":
    if (mode := os.getenv("MODE")) == "UI":
        stream.ui.launch(server_port=7860)
    elif mode == "PHONE":
        stream.fastphone(host="0.0.0.0", port=7860)
    else:
        stream.ui.launch(server_port=7860)
