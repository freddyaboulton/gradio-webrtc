import tempfile

import gradio as gr
import numpy as np
from gradio_webrtc import AdditionalOutputs, ReplyOnPause, WebRTC
from openai import OpenAI
from pydub import AudioSegment

from dotenv import load_dotenv

load_dotenv()


client = OpenAI()


def transcribe(audio: tuple[int, np.ndarray], transcript: list[dict]):
    print("audio", audio)
    segment = AudioSegment(
        audio[1].tobytes(),
        frame_rate=audio[0],
        sample_width=audio[1].dtype.itemsize,
        channels=1,
    )

    transcript.append(
        {"role": "user", "content": gr.Audio((audio[0], audio[1].squeeze()))}
    )

    with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_audio:
        segment.export(temp_audio.name, format="mp3")
        next_chunk = client.audio.transcriptions.create(
            model="whisper-1", file=open(temp_audio.name, "rb")
        ).text
        transcript.append({"role": "assistant", "content": next_chunk})
        yield AdditionalOutputs(transcript)


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

    audio.stream(
        ReplyOnPause(transcribe),
        inputs=[audio, transcript],
        outputs=[audio],
        time_limit=30,
    )
    audio.on_additional_outputs(lambda s: s, outputs=transcript)

if __name__ == "__main__":
    demo.launch()
