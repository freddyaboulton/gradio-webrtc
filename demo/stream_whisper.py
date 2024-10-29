import logging
import tempfile

import gradio as gr
import numpy as np
from dotenv import load_dotenv
from gradio_webrtc import AdditionalOutputs, ReplyOnPause, WebRTC
from openai import OpenAI
from pydub import AudioSegment

load_dotenv()


# Configure the root logger to WARNING to suppress debug messages from other libraries
logging.basicConfig(level=logging.WARNING)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Configure the logger for your specific library
logger = logging.getLogger("gradio_webrtc")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)


client = OpenAI()

def transcribe(audio: tuple[int, np.ndarray]):
    segment = AudioSegment(
       audio[1].tobytes(),
        frame_rate=audio[0],
        sample_width=audio[1].dtype.itemsize,
        channels=1)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_audio:
        segment.export(temp_audio.name, format="mp3")
        next_chunk = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(temp_audio.name, "rb")
        ).text
        yield AdditionalOutputs({"role": "user",
                                   "content": next_chunk})


def update_transcript(transcript: list[dict], next_chunk: dict):
    transcript.append(next_chunk)
    return transcript


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            audio = WebRTC(
                label="Stream",
                mode="send",
                modality="audio",
            )
        with gr.Column():
            transcript = gr.Chatbot(label="transcript", type="messages")
    
    audio.stream(ReplyOnPause(transcribe), inputs=[audio], outputs=[audio])
    audio.change(update_transcript, inputs=transcript, outputs=transcript)

if __name__ == "__main__":
    demo.launch()



