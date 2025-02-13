from fastrtc import Stream, ReplyOnPause
import numpy as np


def detection(audio: tuple[int, np.ndarray]):
    # Implement any iterator that yields audio
    # See "LLM Voice Chat" for a more complete example
    yield audio


stream = Stream(
    handler=ReplyOnPause(detection),
    modality="audio",
    mode="send-receive",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(stream, host="0.0.0.0", port=7860)
