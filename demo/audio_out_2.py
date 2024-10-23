import os

import gradio as gr
import numpy as np
from gradio_webrtc import WebRTC
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
    for _ in range(num_steps):
        segment = AudioSegment.from_file(
            "/Users/freddy/sources/gradio/demo/audio_debugger/cantina.wav"
        )
        yield (
            segment.frame_rate,
            np.array(segment.get_array_of_samples()).reshape(1, -1),
        )
        time.sleep(3.5)


css = """.my-group {max-width: 600px !important; max-height: 600 !important;}
                      .my-column {display: flex !important; justify-content: center !important; align-items: center !important};"""


with gr.Blocks() as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    Audio Streaming (Powered by WebRaTC ⚡️)
    </h1>
    """
    )
    with gr.Row():
        with gr.Column():
            gr.Slider()
        with gr.Column():
            # audio = gr.Audio(interactive=False)
            audio = WebRTC(
                label="Stream",
                rtc_configuration=rtc_configuration,
                mode="receive",
                modality="audio",
            )


if __name__ == "__main__":
    demo.launch()
