import asyncio
import fractions
import logging
import threading
import time
from typing import Callable

import av

logger = logging.getLogger(__name__)


AUDIO_PTIME = 0.020


def player_worker_decode(
    loop,
    next: Callable,
    queue: asyncio.Queue,
    throttle_playback: bool,
    thread_quit: threading.Event,
):
    audio_sample_rate = 48000
    audio_samples = 0
    audio_time_base = fractions.Fraction(1, audio_sample_rate)
    audio_resampler = av.AudioResampler(
        format="s16",
        layout="stereo",
        rate=audio_sample_rate,
        frame_size=int(audio_sample_rate * AUDIO_PTIME),
    )

    frame_time = None
    start_time = time.time()

    while not thread_quit.is_set():
        frame = next()
        logger.debug("emitted %s", frame)
        # read up to 1 second ahead
        if throttle_playback:
            elapsed_time = time.time() - start_time
            if frame_time and frame_time > elapsed_time + 1:
                time.sleep(0.1)
        sample_rate, audio_array = frame
        format = "s16" if audio_array.dtype == "int16" else "fltp"
        frame = av.AudioFrame.from_ndarray(audio_array, format=format, layout="stereo")
        frame.sample_rate = sample_rate
        for frame in audio_resampler.resample(frame):
            # fix timestamps
            frame.pts = audio_samples
            frame.time_base = audio_time_base
            audio_samples += frame.samples

            frame_time = frame.time
            asyncio.run_coroutine_threadsafe(queue.put(frame), loop)
