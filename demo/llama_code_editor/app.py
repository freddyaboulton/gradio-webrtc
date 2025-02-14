from fastrtc import Stream
from fastapi.responses import RedirectResponse
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
    concurrency_limit=10,
    time_limit=90,
)

stream.ui = ui


@stream.get("/")
async def _():
    url = "/ui" if not get_space() else "https://fastrtc-llama-code-editor.hf.space/ui/"
    return RedirectResponse(url)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(stream, host="0.0.0.0", port=7860)
