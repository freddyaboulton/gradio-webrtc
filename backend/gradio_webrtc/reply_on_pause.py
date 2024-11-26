import asyncio
import inspect
from dataclasses import dataclass
from functools import lru_cache
from logging import getLogger
from threading import Event
from typing import Any, Callable, Generator, Literal, Union, cast

import numpy as np

from gradio_webrtc.pause_detection import SileroVADModel, SileroVadOptions
from gradio_webrtc.utils import AdditionalOutputs
from gradio_webrtc.webrtc import StreamHandler

logger = getLogger(__name__)

counter = 0


@lru_cache
def get_vad_model() -> SileroVADModel:
    """Returns the VAD model instance."""
    return SileroVADModel()


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


ReplyFnGenerator = Union[
    # For two arguments
    Callable[
        [tuple[int, np.ndarray], list[dict[Any, Any]]],
        Generator[
            tuple[int, np.ndarray]
            | tuple[int, np.ndarray, Literal["mono", "stereo"]]
            | AdditionalOutputs
            | tuple[tuple[int, np.ndarray], AdditionalOutputs],
            None,
            None,
        ],
    ],
    Callable[
        [tuple[int, np.ndarray]],
        Generator[
            tuple[int, np.ndarray]
            | tuple[int, np.ndarray, Literal["mono", "stereo"]]
            | AdditionalOutputs
            | tuple[tuple[int, np.ndarray], AdditionalOutputs],
            None,
            None,
        ],
    ],
]


class ReplyOnPause(StreamHandler):
    def __init__(
        self,
        fn: ReplyFnGenerator,
        algo_options: AlgoOptions | None = None,
        model_options: SileroVadOptions | None = None,
        expected_layout: Literal["mono", "stereo"] = "mono",
        output_sample_rate: int = 24000,
        output_frame_size: int = 480,
    ):
        super().__init__(expected_layout, output_sample_rate, output_frame_size)
        self.expected_layout: Literal["mono", "stereo"] = expected_layout
        self.output_sample_rate = output_sample_rate
        self.output_frame_size = output_frame_size
        self.model = get_vad_model()
        self.fn = fn
        self.event = Event()
        self.state = AppState()
        self.generator = None
        self.model_options = model_options
        self.algo_options = algo_options or AlgoOptions()
        self.latest_args: list[Any] = []
        self.args_set = Event()

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
        self.args_set.clear()
        self.generator = None
        self.event.clear()
        self.state = AppState()

    def set_args(self, args: list[Any]):
        super().set_args(args)
        self.args_set.set()

    async def fetch_args(
        self,
    ):
        if self.channel:
            self.channel.send("tick")
            logger.debug("Sent tick")

    def emit(self):
        if not self.event.is_set():
            return None
        else:
            if not self.generator:
                if self._needs_additional_inputs and not self.args_set.is_set():
                    asyncio.run_coroutine_threadsafe(self.fetch_args(), self.loop)
                    self.args_set.wait()
                logger.debug("Creating generator")
                audio = cast(np.ndarray, self.state.stream).reshape(1, -1)
                if self._needs_additional_inputs:
                    self.latest_args[0] = (self.state.sampling_rate, audio)
                    self.generator = self.fn(*self.latest_args)
                else:
                    self.generator = self.fn((self.state.sampling_rate, audio))  # type: ignore
                logger.debug("Latest args: %s", self.latest_args)
            self.state.responding = True
            try:
                return next(self.generator)
            except StopIteration:
                self.reset()
