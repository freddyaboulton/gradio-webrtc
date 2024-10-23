import os

import cv2
import gradio as gr
from gradio_webrtc import WebRTC
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


def generation(input_video):
    cap = cv2.VideoCapture(input_video)

    iterating = True

    while iterating:
        iterating, frame = cap.read()

        # flip frame vertically
        frame = cv2.flip(frame, 0)
        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        yield display_frame


with gr.Blocks() as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    Video Streaming (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    with gr.Row():
        with gr.Column():
            input_video = gr.Video(sources="upload")
        with gr.Column():
            output_video = WebRTC(
                label="Video Stream",
                rtc_configuration=rtc_configuration,
                mode="receive",
                modality="video",
            )
            output_video.stream(
                fn=generation,
                inputs=[input_video],
                outputs=[output_video],
                trigger=input_video.upload,
            )


if __name__ == "__main__":
    demo.launch()
