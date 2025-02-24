from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastrtc import Stream
from gradio.utils import get_space

try:
    from demo.llama_code_editor.handler import (
        CodeHandler,
    )
    from demo.llama_code_editor.ui import demo as ui
except (ImportError, ModuleNotFoundError):
    from handler import CodeHandler
    from ui import demo as ui


stream = Stream(
    handler=CodeHandler,
    modality="audio",
    mode="send-receive",
    concurrency_limit=10 if get_space() else None,
    time_limit=90 if get_space() else None,
)

stream.ui = ui

app = FastAPI()


@app.get("/")
async def _():
    url = "/ui" if not get_space() else "https://fastrtc-llama-code-editor.hf.space/ui/"
    return RedirectResponse(url)


if __name__ == "__main__":
    import os

    if (mode := os.getenv("MODE")) == "UI":
        stream.ui.launch(server_port=7860, server_name="0.0.0.0")
    elif mode == "PHONE":
        stream.fastphone(host="0.0.0.0", port=7860)
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=7860)
