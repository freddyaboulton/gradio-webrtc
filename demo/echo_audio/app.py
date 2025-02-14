from fastrtc import Stream, ReplyOnPause, get_twilio_turn_credentials
from fastapi.responses import RedirectResponse
from gradio.utils import get_space
import numpy as np


def detection(audio: tuple[int, np.ndarray]):
    # Implement any iterator that yields audio
    # See "LLM Voice Chat" for a more complete example
    yield audio


stream = Stream(
    handler=ReplyOnPause(detection),
    modality="audio",
    mode="send-receive",
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
    concurrency_limit=20 if get_space() else None,
)


@stream.get("/")
async def index():
    return RedirectResponse(
        url="/ui" if not get_space() else "https://fastrtc-echo-audio.hf.space/ui/"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(stream, host="0.0.0.0", port=7860)
