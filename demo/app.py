import logging

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


import gradio as gr
import numpy as np
from gradio_webrtc import WebRTC, StreamHandler
from queue import Queue
import time


class EchoHandler(StreamHandler):
    def __init__(self) -> None:
        self.queue = Queue()

    def receive(self, frame: tuple[int, np.ndarray] | np.ndarray) -> None:
        self.queue.put(frame)

    def emit(self) -> None:
        return self.queue.get()


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
                rtc_configuration=None,
                mode="send-receive",
                modality="audio",
            )

        audio.stream(fn=EchoHandler(), inputs=[audio], outputs=[audio], time_limit=15)


if __name__ == "__main__":
    demo.launch()
