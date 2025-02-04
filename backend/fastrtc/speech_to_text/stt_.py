from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from ..utils import AudioChunk


@dataclass
class STTModel:
    encoder: Callable
    decoder: Callable


@lru_cache
def get_stt_model() -> STTModel:
    from silero import silero_stt

    model, decoder, _ = silero_stt(language="en", version="v6", jit_model="jit_xlarge")
    return STTModel(model, decoder)


def stt(audio: tuple[int, NDArray[np.int16]]) -> str:
    model = get_stt_model()
    sr, audio_np = audio
    if audio_np.dtype != np.float32:
        print("converting")
        audio_np = audio_np.astype(np.float32) / 32768.0
    try:
        import torch
    except ImportError:
        raise ImportError(
            "PyTorch is required to run speech-to-text for stopword detection. Run `pip install torch`."
        )
    audio_torch = torch.tensor(audio_np, dtype=torch.float32)
    if audio_torch.ndim == 1:
        audio_torch = audio_torch.unsqueeze(0)
    assert audio_torch.ndim == 2, "Audio must have a batch dimension"
    print("before")
    res = model.decoder(model.encoder(audio_torch)[0])
    print("after")
    return res


def stt_for_chunks(
    audio: tuple[int, NDArray[np.int16]], chunks: list[AudioChunk]
) -> str:
    sr, audio_np = audio
    return " ".join(
        [stt((sr, audio_np[chunk["start"] : chunk["end"]])) for chunk in chunks]
    )
