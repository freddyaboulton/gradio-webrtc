import numpy as np
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastrtc import ReplyOnPause, Stream, get_twilio_turn_credentials
from gradio.utils import get_space


def detection(audio: tuple[int, np.ndarray]):
    # Implement any iterator that yields audio
    # See "LLM Voice Chat" for a more complete example
    yield audio


stream = Stream(
    handler=ReplyOnPause(detection),
    modality="audio",
    mode="send-receive",
    rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
    concurrency_limit=5 if get_space() else None,
    time_limit=90 if get_space() else None,
)

app = FastAPI()

stream.mount(app)


@app.get("/")
async def index():
    return RedirectResponse(
        url="/ui" if not get_space() else "https://fastrtc-echo-audio.hf.space/ui/"
    )


if __name__ == "__main__":
    import os

    if (mode := os.getenv("MODE")) == "UI":
        stream.ui.launch(server_port=7860)
    elif mode == "PHONE":
        stream.fastphone(port=7860)
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=7860)
