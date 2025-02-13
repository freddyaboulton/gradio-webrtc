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
## Installation

```bash
pip install gradio_webrtc
```

to use built-in pause detection (see [ReplyOnPause](/user-guide/#reply-on-pause)), install the `vad` extra:

```bash
pip install gradio_webrtc[vad]
```

## Quickstart

Import the [Stream](/userguide/stream) class and pass in a [handler](/userguide/streams/#handlers).
The `Stream` is a [FastAPI](https://fastapi.tiangolo.com/) app that comes with the following routes:

- `/ui`: A Gradio UI for testing your stream.
- `/webrtc/docs`: Documentation and Gradio UI for WebRTC connections.
- `/websocket/docs`: Documentation for WebSocket connections.
- `/telephone/docs`: Documentation for telephone integration.

Launch the stream how you would any FastAPI app. Or use the `fastphone()` method to launch the stream and get a free temporary phone number!


=== "Echo Audio"

    ```python
    from fastrtc import Stream, ReplyOnPause
    from fastapi.responses import HTMLResponse
    import numpy as np

    def detection(audio: tuple[int, np.ndarray]):
        # The function will be passed the audio until the user pauses
        # Implement any iterator that yields audio
        # See "LLM Voice Chat" for a more complete example
        yield audio

    stream = Stream(
        handler=ReplyOnPause(detection),
        modality="audio", 
        mode="send-receive",
    )

    # Optional: Add any routes
    @stream.get("/")
    async def _():
        return HTMLResponse(content=open("index.html").read())

    # launch the stream
    # uvicorn app:stream --host 0.0.0.0 --port 8000
    # OR use fastphone to get a free phone number! (HF token required)
    stream.fastphone()
    ```

=== "Object Detection"

    ```python
    from fastrtc import Stream
    import gradio as gr

    def detection(image, conf_threshold=0.3):
        processed_frame = process_frame(image, conf_threshold)
        return processed_frame

    stream = Stream(
        handler=detection,
        modality="video", 
        mode="send-receive",
        additional_inputs=[
            gr.Slider(minimum=0, maximum=1, step=0.01, value=0.3)
        ]
    )

    # Optional: Add routes
    @stream.get("/")
    async def _():
        return HTMLResponse(content=open("index.html").read())

    # launch the stream
    # uvicorn app:stream --host 0.0.0.0 --port 8000
    ```

=== "LLM Voice Chat"

    ```py
    from fastrtc import (
        ReplyOnPause, AdditionalOutputs, Stream,
        audio_to_bytes, aggregate_bytes_to_16bit
    )
    import gradio as gr
    from groq import Groq
    import anthropic
    from elevenlabs import ElevenLabs

    groq_client = Groq()
    claude_client = anthropic.Anthropic()
    tts_client = ElevenLabs()

    def response(
        audio: tuple[int, np.ndarray], # (1)
        chatbot: list[dict] | None = None, # (2)
    ):
        chatbot = chatbot or []
        messages = [{"role": d["role"], "content": d["content"]} for d in chatbot]
        prompt = groq_client.audio.transcriptions.create(
            file=("audio-file.mp3", audio_to_bytes(audio)),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        ).text
        chatbot.append({"role": "user", "content": prompt})
        messages.append({"role": "user", "content": prompt})
        response = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=512,
            messages=messages,
        )
        response_text = " ".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        )
        chatbot.append({"role": "assistant", "content": response_text})
        yield AdditionalOutputs(chatbot) # (4)
        iterator = tts_client.text_to_speech.convert_as_stream(
            text=response_text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="pcm_24000"
            
        )
        for chunk in aggregate_bytes_to_16bit(iterator):
            audio_array = np.frombuffer(chunk, dtype=np.int16).reshape(1, -1)
            yield (24000, audio_array) # (3)

    chatbot = gr.Chatbot(type="messages")
    stream = Stream(
        modality="audio", # (5)
        mode="send-receive",
        handler=ReplyOnPause(response),
        additional_inputs=[chatbot], # (6)
        additional_outputs=[chatbot],
        additional_outputs_handler=lambda a,b: b,

    )

    # launch the stream
    # uvicorn app:stream --host 0.0.0.0 --port 8000
    ```

    1. The python generator will receive the **entire** audio up until the user stopped. It will be a tuple of the form (sampling_rate, numpy array of audio). The array will have a shape of (1, num_samples).

    2. You can also pass in additional input components. The arguments can be whatever you want but for the automatic Gradio UI to work, the data should match the type expected by a Gradio component.

    3. The generator must yield audio chunks as a tuple of (sampling_rate, numpy audio array). Each numpy audio array must have a shape of (1, num_samples).

    4. You can also yield any additional data as long as it is wrapped in an `AdditionalOutputs` object. Here we yield the latest `chatbot` data which will be displayed in the UI.

    5. We create a `Stream` object with the `mode` and `modality` arguments set to `"send-receive"` and `"audio"`.

    6. We pass in the `chatbot` component as an additional input and output for the automatic Gradio UI to work.

    7. The `Stream` object is a [FastAPI](https://fastapi.tiangolo.com/) app. Run it however you like to run FastAPI apps. Here we use `uvicorn app:stream`.

Learn more about the [Stream](/userguide/streams) in the user guide.
## Key Features

:speaking_head:{ .lg } Automatic Voice Detection and Turn Taking built-in, only worry about the logic for responding to the user.

:material-lightning-bolt:{ .lg } Automatic Gradio UI and API Docs - Go to `http://localhost:8080/webrtc/docs` to try your app with a Gradio UI. The page will also display docs on how to connect with your own javascript frontend over WebRTC.

:simple-webstorm:{ .lg } Automatic WebSocket API - Go to `http://localhost:8080/websocket/docs` to see the docs on how to connect to the server over websockets with your own javascript frontend.

:telephone:{ .lg } Automatic Telephone Support - Us the `fastphone()` method of the stream to launch the application and get a free temporary phone number! Go to `http://localhost:8080/telephone/docs` to see the docs on how to call into the server with your own phone.

:robot:{ .lg } Completely customizable backend - A `Stream` is just a FastAPI app so you can easily extend it to fit your production application. See the [Talk To Claude](/demo/talk_to_claude/app.py) demo for an example on how to serve a custom JS frontend.


## Examples
See the [cookbook](/cookbook).