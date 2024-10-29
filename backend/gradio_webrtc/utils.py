import asyncio
import fractions
import logging
from typing import Any, Callable, Protocol, cast

import av
import numpy as np

logger = logging.getLogger(__name__)


AUDIO_PTIME = 0.020


class AdditionalOutputs:
    def __init__(self, *args) -> None:
        self.args = args


class DataChannel(Protocol):
    def send(self, message: str) -> None: ...


def split_output(data: tuple | Any) -> tuple[Any, AdditionalOutputs | None]:
    if isinstance(data, AdditionalOutputs):
        return None, data
    if isinstance(data, tuple):
        # handle the bare audio case
        if 2 <= len(data) <= 3 and isinstance(data[1], np.ndarray):
            return data, None
        if not len(data) == 2:
            raise ValueError(
                "The tuple must have exactly two elements: the data and an instance of AdditionalOutputs."
            )
        if not isinstance(data[-1], AdditionalOutputs):
            raise ValueError(
                "The last element of the tuple must be an instance of AdditionalOutputs."
            )
        return data[0], cast(AdditionalOutputs, data[1])
    return data, None


async def player_worker_decode(
    next_frame: Callable,
    queue: asyncio.Queue,
    thread_quit: asyncio.Event,
    channel: Callable[[], DataChannel | None] | None,
    set_additional_outputs: Callable | None,
    quit_on_none: bool = False,
    sample_rate: int = 48000,
    frame_size: int = int(48000 * AUDIO_PTIME),
):
    audio_samples = 0
    audio_time_base = fractions.Fraction(1, sample_rate)
    audio_resampler = av.AudioResampler(  # type: ignore
        format="s16",
        layout="stereo",
        rate=sample_rate,
        frame_size=frame_size,
    )

    while not thread_quit.is_set():
        try:
            # Get next frame
            frame, outputs = split_output(
                await asyncio.wait_for(next_frame(), timeout=60)
            )
            if (
                isinstance(outputs, AdditionalOutputs)
                and set_additional_outputs
                and channel
                and channel()
            ):
                set_additional_outputs(outputs)
                cast(DataChannel, channel()).send("change")

            if frame is None:
                if quit_on_none:
                    await queue.put(None)
                    break
                continue

            if len(frame) == 2:
                sample_rate, audio_array = frame
                layout = "mono"
            elif len(frame) == 3:
                sample_rate, audio_array, layout = frame

            logger.debug(
                "received array with shape %s sample rate %s layout %s",
                audio_array.shape,
                sample_rate,
                layout,
            )
            format = "s16" if audio_array.dtype == "int16" else "fltp"

            # Convert to audio frame and resample
            # This runs in the same timeout context
            frame = av.AudioFrame.from_ndarray(  # type: ignore
                audio_array, format=format, layout=layout
            )
            frame.sample_rate = sample_rate

            for processed_frame in audio_resampler.resample(frame):
                processed_frame.pts = audio_samples
                processed_frame.time_base = audio_time_base
                audio_samples += processed_frame.samples
                await queue.put(processed_frame)
            logger.debug("Queue size utils.py: %s", queue.qsize())

        except (TimeoutError, asyncio.TimeoutError):
            logger.warning(
                "Timeout in frame processing cycle after %s seconds - resetting", 60
            )
            continue
        except Exception as e:
            import traceback

            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)
            logger.error("Error processing frame: %s", str(e))
            continue
