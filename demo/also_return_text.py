import logging

# Configure the root logger to WARNING to suppress debug messages from other libraries
logging.basicConfig(level=logging.WARNING)

# Create a console handler
console_handler = logging.FileHandler("gradio_webrtc.log")
console_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Configure the logger for your specific library
logger = logging.getLogger("gradio_webrtc")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)


import os

import gradio as gr
import numpy as np
from gradio_webrtc import WebRTC, AdditionalOutputs
from pydub import AudioSegment
from twilio.rest import Client

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if account_sid and auth_token:
    client = Client(account_sid, auth_token)

    token = client.tokens.create()

    rtc_configuration = {
        "iceServers": token.ice_servers,
        "iceTransportPolicy": "relay",
    }
else:
    rtc_configuration = None

import time


def generation(num_steps):
    for i in range(num_steps):
        segment = AudioSegment.from_file(
            "/Users/freddy/sources/gradio/demo/scratch/audio-streaming/librispeech.mp3"
        )
        yield (
            segment.frame_rate,
            np.array(segment.get_array_of_samples()).reshape(1, -1),
        ), AdditionalOutputs(f"Hello, from step {i}!", "/Users/freddy/sources/gradio/demo/scratch/audio-streaming/librispeech.mp3")

css = """.my-group {max-width: 600px !important; max-height: 600 !important;}
                      .my-column {display: flex !important; justify-content: center !important; align-items: center !important};"""


with gr.Blocks() as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    Audio Streaming (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    with gr.Column(elem_classes=["my-column"]):
        with gr.Group(elem_classes=["my-group"]):
            audio = WebRTC(
                label="Stream",
                rtc_configuration=rtc_configuration,
                mode="receive",
                modality="audio",
            )
            num_steps = gr.Slider(
                label="Number of Steps",
                minimum=1,
                maximum=10,
                step=1,
                value=5,
            )
            button = gr.Button("Generate")
            textbox = gr.Textbox(placeholder="Output will appear here.")
            audio_file = gr.Audio()

        audio.stream(
            fn=generation, inputs=[num_steps], outputs=[audio], trigger=button.click
        )
        audio.change(
            fn=lambda t,a: (f"State changed to {t}.", a),
            outputs=[textbox, audio_file],
        )


if __name__ == "__main__":
    demo.launch(allowed_paths=["/Users/freddy/sources/gradio/demo/scratch/audio-streaming/librispeech.mp3"])
