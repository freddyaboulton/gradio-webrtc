<div style='text-align: center; margin-bottom: 1rem; display: flex; justify-content: center; align-items: center;'>
    <h1 style='color: white; margin: 0;'>FastRTC</h1>
    <img src="/fastrtc_logo.png" 
         onerror="this.onerror=null; this.src='https://huggingface.co/datasets/freddyaboulton/bucket/resolve/main/fastrtc_logo.png';" 
         alt="FastRTC Logo" 
         style="height: 40px; margin-right: 10px;">
</div>

<div style="display: flex; flex-direction: row; justify-content: center">
<img style="display: block; padding-right: 5px; height: 20px;" alt="Static Badge" src="https://img.shields.io/pypi/v/fastrtc"> 
<a href="https://github.com/freddyaboulton/fastrtc" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/github-white?logo=github&logoColor=black"></a>
</div>

<h3 style='text-align: center'>
The Real-Time Communication Library for Python. 
</h3>

Turn any python function into a real-time audio and video stream over WebRTC or WebSockets.

<video src="https://github.com/user-attachments/assets/6fb7f4fe-c5b2-48f3-88ff-f563611812ec" controls></video>

## Installation

```bash
pip install fastrtc
```

to use built-in pause detection (see [ReplyOnPause](userguide/audio/#reply-on-pause)), and text to speech (see [Text To Speech](userguide/audio/#text-to-speech)), install the `vad` and `tts` extras:

```bash
pip install fastrtc[vad, tts]
```

## Quickstart

Import the [Stream](userguide/streams) class and pass in a [handler](userguide/streams/#handlers).
The `Stream` has three main methods:

- `.ui.launch()`: Launch a built-in UI for easily testing and sharing your stream. Built with [Gradio](https://www.gradio.app/).
- `.fastphone()`: Get a free temporary phone number to call into your stream. Hugging Face token required.
- `.mount(app)`: Mount the stream on a [FastAPI](https://fastapi.tiangolo.com/) app. Perfect for integrating with your already existing production system.


=== "Echo Audio"

    ```python
    from fastrtc import Stream, ReplyOnPause
    import numpy as np

    def echo(audio: tuple[int, np.ndarray]):
        # The function will be passed the audio until the user pauses
        # Implement any iterator that yields audio
        # See "LLM Voice Chat" for a more complete example
        yield audio

    stream = Stream(
        handler=ReplyOnPause(detection),
        modality="audio", 
        mode="send-receive",
    )
    ```

=== "LLM Voice Chat"

    ```py
    import os

    from fastrtc import (ReplyOnPause, Stream, get_stt_model, get_tts_model)
    from openai import OpenAI

    sambanova_client = OpenAI(
        api_key=os.getenv("SAMBANOVA_API_KEY"), base_url="https://api.sambanova.ai/v1"
    )
    stt_model = get_stt_model()
    tts_model = get_tts_model()

    def echo(audio):
        prompt = stt_model.stt(audio)
        response = sambanova_client.chat.completions.create(
            model="Meta-Llama-3.2-3B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        prompt = response.choices[0].message.content
        for audio_chunk in tts_model.stream_tts_sync(prompt):
            yield audio_chunk

    stream = Stream(ReplyOnPause(echo), modality="audio", mode="send-receive")
    ```

=== "Webcam Stream"

    ```python
    from fastrtc import Stream
    import numpy as np


    def flip_vertically(image):
        return np.flip(image, axis=0)


    stream = Stream(
        handler=flip_vertically,
        modality="video",
        mode="send-receive",
    )
    ```

=== "Object Detection"

    ```python
    from fastrtc import Stream
    import gradio as gr
    import cv2
    from huggingface_hub import hf_hub_download
    from .inference import YOLOv10

    model_file = hf_hub_download(
        repo_id="onnx-community/yolov10n", filename="onnx/model.onnx"
    )
    
    # git clone https://huggingface.co/spaces/fastrtc/object-detection
    # for YOLOv10 implementation
    model = YOLOv10(model_file)

    def detection(image, conf_threshold=0.3):
        image = cv2.resize(image, (model.input_width, model.input_height))
        new_image = model.detect_objects(image, conf_threshold)
        return cv2.resize(new_image, (500, 500))

    stream = Stream(
        handler=detection,
        modality="video", 
        mode="send-receive",
        additional_inputs=[
            gr.Slider(minimum=0, maximum=1, step=0.01, value=0.3)
        ]
    )
    ```

Run:
=== "UI"

    ```py
    stream.ui.launch()
    ```

=== "Telephone"

    ```py
    stream.fastphone()
    ```

=== "FastAPI"

    ```py
    app = FastAPI()
    stream.mount(app)

    # Optional: Add routes
    @app.get("/")
    async def _():
        return HTMLResponse(content=open("index.html").read())

    # uvicorn app:app --host 0.0.0.0 --port 8000
    ```

Learn more about the [Stream](userguide/streams) in the user guide.
## Key Features

:speaking_head:{ .lg } Automatic Voice Detection and Turn Taking built-in, only worry about the logic for responding to the user.

:material-laptop:{ .lg } Automatic UI - Use the `.ui.launch()` method to launch the webRTC-enabled built-in Gradio UI.

:material-lightning-bolt:{ .lg } Automatic WebRTC Support - Use the `.mount(app)` method to mount the stream on a FastAPI app and get a webRTC endpoint for your own frontend! 

:simple-webstorm:{ .lg } Websocket Support - Use the `.mount(app)` method to mount the stream on a FastAPI app and get a websocket endpoint for your own frontend! 

:telephone:{ .lg } Automatic Telephone Support - Use the `fastphone()` method of the stream to launch the application and get a free temporary phone number!

:robot:{ .lg } Completely customizable backend - A `Stream` can easily be mounted on a FastAPI app so you can easily extend it to fit your production application. See the [Talk To Claude](https://huggingface.co/spaces/fastrtc/talk-to-claude) demo for an example on how to serve a custom JS frontend.


## Examples
See the [cookbook](/cookbook).

Follow and join or [organization](https://huggingface.co/fastrtc) on Hugging Face!

<div style="display: flex; flex-direction: row; justify-content: center; align-items: center; max-width: 600px; margin: 0 auto;">
    <img style="display: block; height: 100px; margin-right: 20px;" src="/hf-logo-with-title.svg">
    <img style="display: block; height: 100px;" src="/gradio-logo-with-title.svg">
</div>
