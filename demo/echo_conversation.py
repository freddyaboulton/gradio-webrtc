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


import time
from queue import Queue

import gradio as gr
import numpy as np
from gradio_webrtc import StreamHandler, WebRTC


class EchoHandler(StreamHandler):
    def __init__(self) -> None:
        super().__init__()
        self.queue = Queue()

    def receive(self, frame: tuple[int, np.ndarray] | np.ndarray) -> None:
        self.queue.put(frame)

    def emit(self) -> None:
        return self.queue.get()


with gr.Blocks() as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    Conversational AI (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    with gr.Column():
        with gr.Group():
            audio = WebRTC(
                label="Stream",
                rtc_configuration=None,
                mode="send-receive",
                modality="audio",
            )

        audio.stream(fn=EchoHandler(), inputs=[audio], outputs=[audio], time_limit=15)


if __name__ == "__main__":
    demo.launch()
