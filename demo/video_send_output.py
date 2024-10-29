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

import cv2
import gradio as gr
from gradio_webrtc import WebRTC, AdditionalOutputs
from huggingface_hub import hf_hub_download
from inference import YOLOv10
from twilio.rest import Client

model_file = hf_hub_download(
    repo_id="onnx-community/yolov10n", filename="onnx/model.onnx"
)

model = YOLOv10(model_file)

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


count = 0
import random


def detection(frame, conf_threshold=0.3):
    frame = cv2.flip(frame, 0)
    global count
    if random.random() > 0.98:
        return AdditionalOutputs(count)    
    count += 1


css = """.my-group {max-width: 600px !important; max-height: 600 !important;}
                      .my-column {display: flex !important; justify-content: center !important; align-items: center !important};"""


with gr.Blocks(css=css) as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    YOLOv10 Webcam Stream (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    gr.HTML(
        """
        <h3 style='text-align: center'>
        <a href='https://arxiv.org/abs/2405.14458' target='_blank'>arXiv</a> | <a href='https://github.com/THU-MIG/yolov10' target='_blank'>github</a>
        </h3>
        """
    )
    with gr.Column(elem_classes=["my-column"]):
        with gr.Group(elem_classes=["my-group"]):
            image = WebRTC(label="Stream", rtc_configuration=rtc_configuration,
                           mode="send")
            conf_threshold = gr.Slider(
                label="Confidence Threshold",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                value=0.30,
            )
            number = gr.Number()

        image.stream(
            fn=detection, inputs=[image, conf_threshold], outputs=[image], time_limit=10
        )
        image.change(lambda n: n, outputs=[number])

demo.launch()
