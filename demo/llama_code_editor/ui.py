from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from fastrtc import WebRTC, get_twilio_turn_credentials
from gradio.utils import get_space

try:
    from demo.llama_code_editor.handler import (
        CodeHandler,
        display_in_sandbox,
        system_prompt,
    )
except (ImportError, ModuleNotFoundError):
    from handler import CodeHandler, display_in_sandbox, system_prompt

load_dotenv()

path = Path(__file__).parent / "assets"

with gr.Blocks(css=".code-component {max-height: 500px !important}") as demo:
    history = gr.State([{"role": "system", "content": system_prompt}])
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML(
                """
                <h1 style='text-align: center'>
                Llama Code Editor
                </h1>
                <h2 style='text-align: center'>
                Powered by SambaNova and Gradio-WebRTC ⚡️
                </h2>
                <p style='text-align: center'>
                Create and edit single-file HTML applications with just your voice!
                </p>
                <p style='text-align: center'>
                Each conversation is limited to 90 seconds. Once the time limit is up you can rejoin the conversation.
                </p>
                """
            )
            webrtc = WebRTC(
                rtc_configuration=get_twilio_turn_credentials()
                if get_space()
                else None,
                mode="send",
                modality="audio",
            )
        with gr.Column(scale=10):
            with gr.Tabs():
                with gr.Tab("Sandbox"):
                    sandbox = gr.HTML(value=open(path / "sandbox.html").read())
                with gr.Tab("Code"):
                    code = gr.Code(
                        language="html",
                        max_lines=50,
                        interactive=False,
                        elem_classes="code-component",
                    )
                with gr.Tab("Chat"):
                    cb = gr.Chatbot(type="messages")

    webrtc.stream(
        CodeHandler,
        inputs=[webrtc, history, code],
        outputs=[webrtc],
        time_limit=90 if get_space() else None,
        concurrency_limit=10 if get_space() else None,
    )
    webrtc.on_additional_outputs(
        lambda history, code: (history, code, history), outputs=[history, code, cb]
    )
    code.change(display_in_sandbox, code, sandbox, queue=False)

if __name__ == "__main__":
    demo.launch()
