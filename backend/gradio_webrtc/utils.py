import asyncio
import fractions
import logging
from typing import Callable

import av

logger = logging.getLogger(__name__)


AUDIO_PTIME = 0.020


async def player_worker_decode(
    next_frame: Callable,
    queue: asyncio.Queue,
    thread_quit: asyncio.Event,
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
            frame = await asyncio.wait_for(next_frame(), timeout=60)

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
                "Timeout in frame processing cycle after %s seconds - resetting", 5
            )
            continue
        except Exception as e:
            import traceback

            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)
            logger.error("Error processing frame: %s", str(e))
            continue
