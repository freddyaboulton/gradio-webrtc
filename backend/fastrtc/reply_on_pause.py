import asyncio
import inspect
from dataclasses import dataclass
from functools import lru_cache
from logging import getLogger
from threading import Event
from typing import Any, AsyncGenerator, Callable, Generator, Literal, cast

import click
import numpy as np
from numpy.typing import NDArray

from .pause_detection import SileroVADModel, SileroVadOptions
from .tracks import EmitType, StreamHandler
from .utils import create_message, split_output

logger = getLogger(__name__)

counter = 0


@lru_cache
def get_vad_model() -> SileroVADModel:
    """Returns the VAD model instance and warms it up with dummy data."""
    try:
        import importlib.util

        mod = importlib.util.find_spec("onnxruntime")
        if mod is None:
            raise RuntimeError("Install fastrtc[vad] to use ReplyOnPause")
    except (ValueError, ModuleNotFoundError):
        raise RuntimeError("Install fastrtc[vad] to use ReplyOnPause")
    model = SileroVADModel()
    # Warm up the model with dummy data
    print(click.style("INFO", fg="green") + ":\t  Warming up VAD model.")
    for _ in range(10):
        dummy_audio = np.zeros(102400, dtype=np.float32)
        model.vad((24000, dummy_audio), None)
    print(click.style("INFO", fg="green") + ":\t  VAD model warmed up.")
    return model


@dataclass
class AlgoOptions:
    """Algorithm options."""

    audio_chunk_duration: float = 0.6
    started_talking_threshold: float = 0.2
    speech_threshold: float = 0.1


@dataclass
class AppState:
    stream: np.ndarray | None = None
    sampling_rate: int = 0
    pause_detected: bool = False
    started_talking: bool = False
    responding: bool = False
    stopped: bool = False
    buffer: np.ndarray | None = None
    responded_audio: bool = False


ReplyFnGenerator = (
    Callable[
        [tuple[int, NDArray[np.int16]], list[dict[Any, Any]]],
        Generator[EmitType, None, None],
    ]
    | Callable[
        [tuple[int, NDArray[np.int16]]],
        Generator[EmitType, None, None],
    ]
    | Callable[
        [tuple[int, NDArray[np.int16]]],
        AsyncGenerator[EmitType, None],
    ]
    | Callable[
        [tuple[int, NDArray[np.int16]], list[dict[Any, Any]]],
        AsyncGenerator[EmitType, None],
    ]
)


async def iterate(generator: Generator) -> Any:
    return next(generator)


class ReplyOnPause(StreamHandler):
    def __init__(
        self,
        fn: ReplyFnGenerator,
        algo_options: AlgoOptions | None = None,
        model_options: SileroVadOptions | None = None,
        expected_layout: Literal["mono", "stereo"] = "mono",
        output_sample_rate: int = 24000,
        output_frame_size: int = 480,
        input_sample_rate: int = 48000,
    ):
        super().__init__(
            expected_layout,
            output_sample_rate,
            output_frame_size,
            input_sample_rate=input_sample_rate,
        )
        self.expected_layout: Literal["mono", "stereo"] = expected_layout
        self.output_sample_rate = output_sample_rate
        self.output_frame_size = output_frame_size
        self.model = get_vad_model()
        self.fn = fn
        self.is_async = inspect.isasyncgenfunction(fn)
        self.event = Event()
        self.state = AppState()
        self.generator: Generator[EmitType, None, None] | None = None
        self.model_options = model_options
        self.algo_options = algo_options or AlgoOptions()

    @property
    def _needs_additional_inputs(self) -> bool:
        return len(inspect.signature(self.fn).parameters) > 1

    def copy(self):
        return ReplyOnPause(
            self.fn,
            self.algo_options,
            self.model_options,
            self.expected_layout,
            self.output_sample_rate,
            self.output_frame_size,
            self.input_sample_rate,
        )

    def determine_pause(
        self, audio: np.ndarray, sampling_rate: int, state: AppState
    ) -> bool:
        """Take in the stream, determine if a pause happened"""
        duration = len(audio) / sampling_rate

        if duration >= self.algo_options.audio_chunk_duration:
            dur_vad = self.model.vad((sampling_rate, audio), self.model_options)
            logger.debug("VAD duration: %s", dur_vad)
            if (
                dur_vad > self.algo_options.started_talking_threshold
                and not state.started_talking
            ):
                state.started_talking = True
                logger.debug("Started talking")
            if state.started_talking:
                if state.stream is None:
                    state.stream = audio
                else:
                    state.stream = np.concatenate((state.stream, audio))
            state.buffer = None
            if dur_vad < self.algo_options.speech_threshold and state.started_talking:
                return True
        return False

    def process_audio(self, audio: tuple[int, np.ndarray], state: AppState) -> None:
        frame_rate, array = audio
        array = np.squeeze(array)
        if not state.sampling_rate:
            state.sampling_rate = frame_rate
        if state.buffer is None:
            state.buffer = array
        else:
            state.buffer = np.concatenate((state.buffer, array))

        pause_detected = self.determine_pause(
            state.buffer, state.sampling_rate, self.state
        )
        state.pause_detected = pause_detected

    def receive(self, frame: tuple[int, np.ndarray]) -> None:
        if self.state.responding:
            return
        self.process_audio(frame, self.state)
        if self.state.pause_detected:
            self.event.set()

    def reset(self):
        super().reset()
        if self.phone_mode:
            self.args_set.set()
        self.generator = None
        self.event.clear()
        self.state = AppState()

    async def async_iterate(self, generator) -> EmitType:
        return await anext(generator)

    def emit(self):
        if not self.event.is_set():
            return None
        else:
            if not self.generator:
                self.send_message_sync(create_message("log", "pause_detected"))
                if self._needs_additional_inputs and not self.args_set.is_set():
                    if not self.phone_mode:
                        self.wait_for_args_sync()
                    else:
                        self.latest_args = [None]
                        self.args_set.set()
                logger.debug("Creating generator")
                audio = cast(np.ndarray, self.state.stream).reshape(1, -1)
                if self._needs_additional_inputs:
                    self.latest_args[0] = (self.state.sampling_rate, audio)
                    self.generator = self.fn(*self.latest_args)  # type: ignore
                else:
                    self.generator = self.fn((self.state.sampling_rate, audio))  # type: ignore
                logger.debug("Latest args: %s", self.latest_args)
            self.state.responding = True
            try:
                if self.is_async:
                    output = asyncio.run_coroutine_threadsafe(
                        self.async_iterate(self.generator), self.loop
                    ).result()
                else:
                    output = next(self.generator)  # type: ignore
                audio, additional_outputs = split_output(output)
                if audio is not None:
                    self.send_message_sync(create_message("log", "response_starting"))
                    self.state.responded_audio = True
                if self.phone_mode:
                    if additional_outputs:
                        self.latest_args = [None] + list(additional_outputs.args)
                return output
            except (StopIteration, StopAsyncIteration):
                if not self.state.responded_audio:
                    self.send_message_sync(create_message("log", "response_starting"))
                self.reset()
            except Exception as e:
                import traceback

                traceback.print_exc()
                logger.debug("Error in ReplyOnPause: %s", e)
                self.reset()
