import logging
import warnings
from dataclasses import dataclass
from typing import List

import numpy as np
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# The code below is adapted from https://github.com/snakers4/silero-vad.
# The code below is adapted from https://github.com/gpt-omni/mini-omni/blob/main/utils/vad.py


@dataclass
class SileroVadOptions:
    """VAD options.

    Attributes:
      threshold: Speech threshold. Silero VAD outputs speech probabilities for each audio chunk,
        probabilities ABOVE this value are considered as SPEECH. It is better to tune this
        parameter for each dataset separately, but "lazy" 0.5 is pretty good for most datasets.
      min_speech_duration_ms: Final speech chunks shorter min_speech_duration_ms are thrown out.
      max_speech_duration_s: Maximum duration of speech chunks in seconds. Chunks longer
        than max_speech_duration_s will be split at the timestamp of the last silence that
        lasts more than 100ms (if any), to prevent aggressive cutting. Otherwise, they will be
        split aggressively just before max_speech_duration_s.
      min_silence_duration_ms: In the end of each speech chunk wait for min_silence_duration_ms
        before separating it
      window_size_samples: Audio chunks of window_size_samples size are fed to the silero VAD model.
        WARNING! Silero VAD models were trained using 512, 1024, 1536 samples for 16000 sample rate.
        Values other than these may affect model performance!!
      speech_pad_ms: Final speech chunks are padded by speech_pad_ms each side
      speech_duration: If the length of the speech is less than this value, a pause will be detected.
    """

    threshold: float = 0.5
    min_speech_duration_ms: int = 250
    max_speech_duration_s: float = float("inf")
    min_silence_duration_ms: int = 2000
    window_size_samples: int = 1024
    speech_pad_ms: int = 400


class SileroVADModel:
    @staticmethod
    def download_model() -> str:
        return hf_hub_download(
            repo_id="freddyaboulton/silero-vad", filename="silero_vad.onnx"
        )

    def __init__(self):
        try:
            import onnxruntime
        except ImportError as e:
            raise RuntimeError(
                "Applying the VAD filter requires the onnxruntime package"
            ) from e

        path = self.download_model()

        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        opts.log_severity_level = 4

        self.session = onnxruntime.InferenceSession(
            path,
            providers=["CPUExecutionProvider"],
            sess_options=opts,
        )

    def get_initial_state(self, batch_size: int):
        h = np.zeros((2, batch_size, 64), dtype=np.float32)
        c = np.zeros((2, batch_size, 64), dtype=np.float32)
        return h, c

    @staticmethod
    def collect_chunks(audio: np.ndarray, chunks: List[dict]) -> np.ndarray:
        """Collects and concatenates audio chunks."""
        if not chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(
            [audio[chunk["start"] : chunk["end"]] for chunk in chunks]
        )

    def get_speech_timestamps(
        self,
        audio: np.ndarray,
        vad_options: SileroVadOptions,
        **kwargs,
    ) -> List[dict]:
        """This method is used for splitting long audios into speech chunks using silero VAD.

        Args:
        audio: One dimensional float array.
        vad_options: Options for VAD processing.
        kwargs: VAD options passed as keyword arguments for backward compatibility.

        Returns:
        List of dicts containing begin and end samples of each speech chunk.
        """

        threshold = vad_options.threshold
        min_speech_duration_ms = vad_options.min_speech_duration_ms
        max_speech_duration_s = vad_options.max_speech_duration_s
        min_silence_duration_ms = vad_options.min_silence_duration_ms
        window_size_samples = vad_options.window_size_samples
        speech_pad_ms = vad_options.speech_pad_ms

        if window_size_samples not in [512, 1024, 1536]:
            warnings.warn(
                "Unusual window_size_samples! Supported window_size_samples:\n"
                " - [512, 1024, 1536] for 16000 sampling_rate"
            )

        sampling_rate = 16000
        min_speech_samples = sampling_rate * min_speech_duration_ms / 1000
        speech_pad_samples = sampling_rate * speech_pad_ms / 1000
        max_speech_samples = (
            sampling_rate * max_speech_duration_s
            - window_size_samples
            - 2 * speech_pad_samples
        )
        min_silence_samples = sampling_rate * min_silence_duration_ms / 1000
        min_silence_samples_at_max_speech = sampling_rate * 98 / 1000

        audio_length_samples = len(audio)

        state = self.get_initial_state(batch_size=1)

        speech_probs = []
        for current_start_sample in range(0, audio_length_samples, window_size_samples):
            chunk = audio[
                current_start_sample : current_start_sample + window_size_samples
            ]
            if len(chunk) < window_size_samples:
                chunk = np.pad(chunk, (0, int(window_size_samples - len(chunk))))
            speech_prob, state = self(chunk, state, sampling_rate)
            speech_probs.append(speech_prob)

        triggered = False
        speeches = []
        current_speech = {}
        neg_threshold = threshold - 0.15

        # to save potential segment end (and tolerate some silence)
        temp_end = 0
        # to save potential segment limits in case of maximum segment size reached
        prev_end = next_start = 0

        for i, speech_prob in enumerate(speech_probs):
            if (speech_prob >= threshold) and temp_end:
                temp_end = 0
                if next_start < prev_end:
                    next_start = window_size_samples * i

            if (speech_prob >= threshold) and not triggered:
                triggered = True
                current_speech["start"] = window_size_samples * i
                continue

            if (
                triggered
                and (window_size_samples * i) - current_speech["start"]
                > max_speech_samples
            ):
                if prev_end:
                    current_speech["end"] = prev_end
                    speeches.append(current_speech)
                    current_speech = {}
                    # previously reached silence (< neg_thres) and is still not speech (< thres)
                    if next_start < prev_end:
                        triggered = False
                    else:
                        current_speech["start"] = next_start
                    prev_end = next_start = temp_end = 0
                else:
                    current_speech["end"] = window_size_samples * i
                    speeches.append(current_speech)
                    current_speech = {}
                    prev_end = next_start = temp_end = 0
                    triggered = False
                    continue

            if (speech_prob < neg_threshold) and triggered:
                if not temp_end:
                    temp_end = window_size_samples * i
                # condition to avoid cutting in very short silence
                if (
                    window_size_samples * i
                ) - temp_end > min_silence_samples_at_max_speech:
                    prev_end = temp_end
                if (window_size_samples * i) - temp_end < min_silence_samples:
                    continue
                else:
                    current_speech["end"] = temp_end
                    if (
                        current_speech["end"] - current_speech["start"]
                    ) > min_speech_samples:
                        speeches.append(current_speech)
                    current_speech = {}
                    prev_end = next_start = temp_end = 0
                    triggered = False
                    continue

        if (
            current_speech
            and (audio_length_samples - current_speech["start"]) > min_speech_samples
        ):
            current_speech["end"] = audio_length_samples
            speeches.append(current_speech)

        for i, speech in enumerate(speeches):
            if i == 0:
                speech["start"] = int(max(0, speech["start"] - speech_pad_samples))
            if i != len(speeches) - 1:
                silence_duration = speeches[i + 1]["start"] - speech["end"]
                if silence_duration < 2 * speech_pad_samples:
                    speech["end"] += int(silence_duration // 2)
                    speeches[i + 1]["start"] = int(
                        max(0, speeches[i + 1]["start"] - silence_duration // 2)
                    )
                else:
                    speech["end"] = int(
                        min(audio_length_samples, speech["end"] + speech_pad_samples)
                    )
                    speeches[i + 1]["start"] = int(
                        max(0, speeches[i + 1]["start"] - speech_pad_samples)
                    )
            else:
                speech["end"] = int(
                    min(audio_length_samples, speech["end"] + speech_pad_samples)
                )

        return speeches

    def vad(
        self,
        audio_tuple: tuple[int, np.ndarray],
        vad_parameters: None | SileroVadOptions,
    ) -> float:
        sampling_rate, audio = audio_tuple
        logger.debug("VAD audio shape input: %s", audio.shape)
        try:
            audio = audio.astype(np.float32) / 32768.0
            sr = 16000
            if sr != sampling_rate:
                try:
                    import librosa  # type: ignore
                except ImportError as e:
                    raise RuntimeError(
                        "Applying the VAD filter requires the librosa if the input sampling rate is not 16000hz"
                    ) from e
                audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=sr)

            if not vad_parameters:
                vad_parameters = SileroVadOptions()
            speech_chunks = self.get_speech_timestamps(audio, vad_parameters)
            logger.debug("VAD speech chunks: %s", speech_chunks)
            audio = self.collect_chunks(audio, speech_chunks)
            logger.debug("VAD audio shape: %s", audio.shape)
            duration_after_vad = audio.shape[0] / sr

            return duration_after_vad
        except Exception as e:
            import math
            import traceback

            logger.debug("VAD Exception: %s", str(e))
            exec = traceback.format_exc()
            logger.debug("traceback %s", exec)
            return math.inf

    def __call__(self, x, state, sr: int):
        if len(x.shape) == 1:
            x = np.expand_dims(x, 0)
        if len(x.shape) > 2:
            raise ValueError(
                f"Too many dimensions for input audio chunk {len(x.shape)}"
            )
        if sr / x.shape[1] > 31.25:
            raise ValueError("Input audio chunk is too short")

        h, c = state

        ort_inputs = {
            "input": x,
            "h": h,
            "c": c,
            "sr": np.array(sr, dtype="int64"),
        }

        out, h, c = self.session.run(None, ort_inputs)
        state = (h, c)

        return out, state
