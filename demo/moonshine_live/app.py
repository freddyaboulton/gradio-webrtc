from functools import lru_cache
from typing import Generator, Literal

import gradio as gr
import numpy as np
from fastrtc import (
    AdditionalOutputs,
    ReplyOnPause,
    Stream,
    audio_to_float32,
    get_twilio_turn_credentials,
)
from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
from numpy.typing import NDArray


@lru_cache(maxsize=None)
def load_moonshine(
    model_name: Literal["moonshine/base", "moonshine/tiny"],
) -> MoonshineOnnxModel:
    return MoonshineOnnxModel(model_name=model_name)


tokenizer = load_tokenizer()


def stt(
    audio: tuple[int, NDArray[np.int16 | np.float32]],
    model_name: Literal["moonshine/base", "moonshine/tiny"],
) -> Generator[AdditionalOutputs, None, None]:
    moonshine = load_moonshine(model_name)
    sr, audio_np = audio  # type: ignore
    if audio_np.dtype == np.int16:
        audio_np = audio_to_float32(audio)
    if audio_np.ndim == 1:
        audio_np = audio_np.reshape(1, -1)
    tokens = moonshine.generate(audio_np)
    yield AdditionalOutputs(tokenizer.decode_batch(tokens)[0])


stream = Stream(
    ReplyOnPause(stt, input_sample_rate=16000),
    modality="audio",
    mode="send",
    ui_args={
        "title": "Live Captions by Moonshine",
        "icon": "default-favicon.ico",
        "icon_button_color": "#5c5c5c",
        "pulse_color": "#a7c6fc",
        "icon_radius": 0,
    },
    rtc_configuration=get_twilio_turn_credentials(),
    additional_inputs=[
        gr.Radio(
            choices=["moonshine/base", "moonshine/tiny"],
            value="moonshine/base",
            label="Model",
        )
    ],
    additional_outputs=[gr.Textbox(label="Captions")],
    additional_outputs_handler=lambda prev, current: (prev + "\n" + current).strip(),
)

if __name__ == "__main__":
    stream.ui.launch()
