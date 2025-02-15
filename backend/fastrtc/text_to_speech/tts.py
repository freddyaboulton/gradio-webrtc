import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import AsyncGenerator, Generator, Literal, Protocol

import numpy as np
from huggingface_hub import hf_hub_download
from numpy.typing import NDArray


class TTSOptions:
    pass


class TTSModel(Protocol):
    def tts(self, text: str) -> tuple[int, NDArray[np.float32]]: ...

    async def stream_tts(
        self, text: str, options: TTSOptions | None = None
    ) -> AsyncGenerator[tuple[int, NDArray[np.float32]], None]: ...

    def stream_tts_sync(
        self, text: str, options: TTSOptions | None = None
    ) -> Generator[tuple[int, NDArray[np.float32]], None, None]: ...


@dataclass
class KokoroTTSOptions(TTSOptions):
    voice: str = "af_heart"
    speed: float = 1.0
    lang: str = "en-us"


@lru_cache
def get_tts_model(model: Literal["kokoro"] = "kokoro") -> TTSModel:
    m = KokoroTTSModel()
    m.tts("Hello, world!")
    return m


class KokoroTTSModel(TTSModel):
    def __init__(self):
        from kokoro_onnx import Kokoro

        self.model = Kokoro(
            model_path=hf_hub_download("fastrtc/kokoro-onnx", "kokoro-v1.0.onnx"),
            voices_path=hf_hub_download("fastrtc/kokoro-onnx", "voices-v1.0.bin"),
        )

    def tts(
        self, text: str, options: KokoroTTSOptions | None = None
    ) -> tuple[int, NDArray[np.float32]]:
        options = options or KokoroTTSOptions()
        a, b = self.model.create(
            text, voice=options.voice, speed=options.speed, lang=options.lang
        )
        return b, a

    async def stream_tts(
        self, text: str, options: KokoroTTSOptions | None = None
    ) -> AsyncGenerator[tuple[int, NDArray[np.float32]], None]:
        options = options or KokoroTTSOptions()

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        for s_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            chunk_idx = 0
            async for chunk in self.model.create_stream(
                sentence, voice=options.voice, speed=options.speed, lang=options.lang
            ):
                if s_idx != 0 and chunk_idx == 0:
                    yield chunk[1], np.zeros(chunk[1] // 7, dtype=np.float32)
                yield chunk[1], chunk[0]

    def stream_tts_sync(
        self, text: str, options: KokoroTTSOptions | None = None
    ) -> Generator[tuple[int, NDArray[np.float32]], None, None]:
        loop = asyncio.new_event_loop()

        # Use the new loop to run the async generator
        iterator = self.stream_tts(text, options).__aiter__()
        while True:
            try:
                yield loop.run_until_complete(iterator.__anext__())
            except StopAsyncIteration:
                break
