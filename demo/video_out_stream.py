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


def generation():
    url = "https://download.tsi.telecom-paristech.fr/gpac/dataset/dash/uhd/mux_sources/hevcds_720p30_2M.mp4"
    cap = cv2.VideoCapture(url)
    iterating = True
    while iterating:
        iterating, frame = cap.read()
        yield frame


with gr.Blocks() as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    Video Streaming (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    output_video = WebRTC(
        label="Video Stream",
        rtc_configuration=rtc_configuration,
        mode="receive",
        modality="video",
    )
    button = gr.Button("Start", variant="primary")
    output_video.stream(
        fn=generation, inputs=None, outputs=[output_video], trigger=button.click
    )


if __name__ == "__main__":
    demo.launch()
