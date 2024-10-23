import asyncio
import fractions
import logging
import threading
from typing import Callable

import av

logger = logging.getLogger(__name__)


AUDIO_PTIME = 0.020


def player_worker_decode(
    loop,
    next_frame: Callable,
    queue: asyncio.Queue,
    thread_quit: threading.Event,
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
        frame = next_frame()
        if frame is None:
            if quit_on_none:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
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

        frame = av.AudioFrame.from_ndarray(audio_array, format=format, layout=layout)  # type: ignore
        frame.sample_rate = sample_rate
        for frame in audio_resampler.resample(frame):
            # fix timestamps
            frame.pts = audio_samples
            frame.time_base = audio_time_base
            audio_samples += frame.samples
            asyncio.run_coroutine_threadsafe(queue.put(frame), loop)
            logger.debug("Queue size utils.py: %s", queue.qsize())
