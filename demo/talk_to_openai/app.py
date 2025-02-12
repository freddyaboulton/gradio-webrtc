import asyncio
import base64
from pathlib import Path

import gradio as gr
import numpy as np
import openai
from dotenv import load_dotenv
from fastrtc import (
    AdditionalOutputs,
    AsyncStreamHandler,
    Stream,
)
from fastapi.responses import HTMLResponse, StreamingResponse

from openai.types.beta.realtime import ResponseAudioTranscriptDoneEvent

load_dotenv()

cur_dir = Path(__file__).parent

SAMPLE_RATE = 24000


class OpenAIHandler(AsyncStreamHandler):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            expected_layout="mono",
            output_sample_rate=SAMPLE_RATE,
            output_frame_size=480,
            input_sample_rate=SAMPLE_RATE,
        )
        self.connection = None
        self.connected = asyncio.Event()
        self.output_queue = asyncio.Queue()

    def copy(self):
        return OpenAIHandler()

    async def _initialize_connection(
        self,
    ):
        """Connect to realtime API. Run forever in separate thread to keep connection open."""
        self.client = openai.AsyncOpenAI()
        async with self.client.beta.realtime.connect(
            model="gpt-4o-mini-realtime-preview-2024-12-17"
        ) as conn:
            await conn.session.update(
                session={"turn_detection": {"type": "server_vad"}}
            )
            self.connection = conn
            self.connected.set()
            async for event in self.connection:
                if event.type == "response.audio_transcript.done":
                    await self.output_queue.put(AdditionalOutputs(event))
                if event.type == "response.audio.delta":
                    await self.output_queue.put(
                        (
                            self.output_sample_rate,
                            np.frombuffer(
                                base64.b64decode(event.delta), dtype=np.int16
                            ).reshape(1, -1),
                        ),
                    )

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        if not self.connection:
            await self.fetch_args()
            asyncio.create_task(self._initialize_connection())
            await self.connected.wait()
        try:
            _, array = frame
            array = array.squeeze()
            audio_message = base64.b64encode(array.tobytes()).decode("utf-8")
            await self.connection.input_audio_buffer.append(audio=audio_message)  # type: ignore
        except Exception as e:
            # print traceback
            print(f"Error in receive: {str(e)}")
            import traceback

            traceback.print_exc()

    async def emit(self) -> tuple[int, np.ndarray] | AdditionalOutputs | None:
        if not self.connection:
            return None
        return await self.output_queue.get()

    def reset_state(self):
        """Reset connection state for new recording session"""
        self.connection = None
        self.args_set.clear()
        self.connected.clear()

    async def shutdown(self) -> None:
        if self.connection:
            await self.connection.close()
            self.reset_state()


def update_chatbot(chatbot: list[dict], response: ResponseAudioTranscriptDoneEvent):
    chatbot.append({"role": "assistant", "content": response.transcript})
    return chatbot


chatbot = gr.Chatbot(type="messages")
latest_message = gr.Textbox(type="text", visible=False)
stream = Stream(
    OpenAIHandler(),
    mode="send-receive",
    modality="audio",
    additional_inputs=[chatbot],
    additional_outputs=[chatbot],
    additional_outputs_handler=update_chatbot,
)


@stream.get("/")
async def _():
    return HTMLResponse(content=open(cur_dir / "index.html").read())


@stream.get("/outputs")
def _(webrtc_id: str):
    async def output_stream():
        import json

        async for output in stream.output_stream(webrtc_id):
            s = json.dumps({"role": "assistant", "content": output.args[0].transcript})
            yield f"event: output\ndata: {s}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")
