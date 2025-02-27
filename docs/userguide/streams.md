# Core Concepts


The core of FastRTC is the `Stream` object. It can be used to stream audio, video, or both.

Here's a simple example of creating a video stream that flips the video vertically. We'll use it to explain the core concepts of the `Stream` object. Click on the plus icons to get a link to the relevant section.

```python
from fastrtc import Stream
import gradio as gr
import numpy as np

def detection(image, slider):
    return np.flip(image, axis=0)

stream = Stream(
    handler=detection, # (1)
    modality="video", # (2)
    mode="send-receive", # (3)
    additional_inputs=[
        gr.Slider(minimum=0, maximum=1, step=0.01, value=0.3) # (4)
    ],
    additional_outputs=None, # (5)
    additional_outputs_handler=None # (6)
)
```

1. See [Handlers](#handlers) for more information.
2. See [Modalities](#modalities) for more information.
3. See [Stream Modes](#stream-modes) for more information.
4. See [Additional Inputs](#additional-inputs) for more information.
5. See [Additional Outputs](#additional-outputs) for more information.
6. See [Additional Outputs Handler](#additional-outputs) for more information.
7. Mount the `Stream` on a `FastAPI` app with `stream.mount(app)` and you can add custom routes to it. See [Custom Routes and Frontend Integration](#custom-routes-and-frontend-integration) for more information.
8. See [Built-in Routes](#built-in-routes) for more information.

Run:
=== "UI"

    ```py
    stream.ui.launch()
    ```
=== "FastAPI"

    ```py
    app = FastAPI()
    stream.mount(app)

    # uvicorn app:app --host 0.0.0.0 --port 8000
    ```

### Stream Modes

FastRTC supports three streaming modes:

- `send-receive`: Bidirectional streaming (default)
- `send`: Client-to-server only 
- `receive`: Server-to-client only

### Modalities

FastRTC supports three modalities:

- `video`: Video streaming
- `audio`: Audio streaming  
- `audio-video`: Combined audio and video streaming

### Handlers

The `handler` argument is the main argument of the `Stream` object. A handler should be a function or a class that inherits from `StreamHandler` or `AsyncStreamHandler` depending on the modality and mode.


| Modality | send-receive | send | receive |
|----------|--------------|------|----------|
| video | Function that takes a video frame and returns a new video frame | Function that takes a video frame and returns a new frame | Function that takes a video frame and returns a new frame |
| audio | `StreamHandler` or `AsyncStreamHandler` subclass | `StreamHandler` or `AsyncStreamHandler` subclass | Generator yielding audio frames |
| audio-video | `AudioVideoStreamHandler` or `AsyncAudioVideoStreamHandler` subclass | Not Supported Yet | Not Supported Yet |


## Methods

The `Stream` has three main methods:

- `.ui.launch()`: Launch a built-in UI for easily testing and sharing your stream. Built with [Gradio](https://www.gradio.app/). You can change the UI by setting the `ui` property of the `Stream` object. Also see the [Gradio guide](../gradio.md) for building Gradio apss with fastrtc.
- `.fastphone()`: Get a free temporary phone number to call into your stream. Hugging Face token required.
- `.mount(app)`: Mount the stream on a [FastAPI](https://fastapi.tiangolo.com/) app. Perfect for integrating with your already existing production system or for building a custom UI.

!!! warning
    Websocket docs are only available for audio streams. Telephone docs are only available for audio streams in `send-receive` mode.

## Additional Inputs

You can add additional inputs to your stream using the `additional_inputs` argument. These inputs will be displayed in the generated Gradio UI and they will be passed to the handler as additional arguments.

!!! tip
    For audio `StreamHandlers`, please read the special [note](../audio#requesting-inputs) on requesting inputs.

In the automatic gradio UI, these inputs will be the same python type corresponding to the Gradio component. In our case, we used a `gr.Slider` as the additional input, so it will be passed as a float. See the [Gradio documentation](https://www.gradio.app/docs/gradio) for a complete list of components and their corresponding types.

### Input Hooks

Outside of the gradio UI, you are free to update the inputs however you like by using the `set_input` method of the `Stream` object.

A common pattern is to use a `POST` request to send the updated data.

```python
from pydantic import BaseModel, Field
from fastapi import FastAPI

class InputData(BaseModel):
    webrtc_id: str
    conf_threshold: float = Field(ge=0, le=1)

app = FastAPI()
stream.mount(app)

@app.post("/input_hook")
async def _(data: InputData):
    stream.set_input(data.webrtc_id, data.conf_threshold)
```

The updated data will be passed to the handler on the **next** call.


## Additional Outputs

You can return additional output from the handler by returning an instance of `AdditionalOutputs` from the handler.
Let's modify our previous example to also return the number of detections in the frame.

```python
from fastrtc import Stream, AdditionalOutputs
import gradio as gr

def detection(image, conf_threshold=0.3):
    processed_frame, n_objects = process_frame(image, conf_threshold)
    return processed_frame, AdditionalOutputs(n_objects)

stream = Stream(
    handler=detection,
    modality="video",
    mode="send-receive",
    additional_inputs=[
        gr.Slider(minimum=0, maximum=1, step=0.01, value=0.3)
    ],
    additional_outputs=[gr.Number()], # (5)
    additional_outputs_handler=lambda component, n_objects: n_objects
)
```

We added a `gr.Number()` to the additional outputs and we provided an `additional_outputs_handler`.

The `additional_outputs_handler` is **only** needed for the gradio UI. It is a function that takes the current state of the `component` and the instance of `AdditionalOutputs` and returns the updated state of the `component`. In our case, we want to update the `gr.Number()` with the number of detections.

!!! tip
    Since the webRTC is very low latency, you probably don't want to return an additional output on each frame. 

### Output Hooks

Outside of the gradio UI, you are free to access the output data however you like by calling the `output_stream` method of the `Stream` object.

A common pattern is to use a `GET` request to get a stream of the output data.

```python
from fastapi.responses import StreamingResponse

@app.get("/updates")
async def stream_updates(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            # Output is the AdditionalOutputs instance
            # Be sure to serialize it however you would like
            yield f"data: {output.args[0]}\n\n"

    return StreamingResponse(
        output_stream(), 
        media_type="text/event-stream"
    )
```

## Custom Routes and Frontend Integration

You can add custom routes for serving your own frontend or handling additional functionality once you have mounted the stream on a FastAPI app.

```python
from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from fastrtc import Stream

stream = Stream(...)

app = FastAPI()
stream.mount(app)

# Serve a custom frontend
@app.get("/")
async def serve_frontend():
    return HTMLResponse(content=open("index.html").read())

```

## Telephone Integration

FastRTC provides built-in telephone support through the `fastphone()` method:

```python
# Launch with a temporary phone number
stream.fastphone(
    # Optional: If None, will use the default token in your machine or read from the HF_TOKEN environment variable
    token="your_hf_token",  
    host="127.0.0.1",
    port=8000
)
```

This will print out a phone number along with your temporary code you can use to connect to the stream. You are limited to **10 minutes** of calls per calendar month.

!!! warning

    See this [section](../audio#telephone-integration) on making sure your stream handler is compatible for telephone usage.

!!! tip

    If you don't have a HF token, you can get one [here](https://huggingface.co/settings/tokens).

## Concurrency

1. You can limit the number of concurrent connections by setting the `concurrency_limit` argument.
2. You can limit the amount of time (in seconds) a connection can stay open by setting the `time_limit` argument.

```python
stream = Stream(
    handler=handler,
    concurrency_limit=10,
    time_limit=3600
)
```