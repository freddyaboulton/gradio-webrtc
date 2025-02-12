# Stream


The core of FastRTC is the `Stream` object. It is a [FastAPI](https://fastapi.tiangolo.com/) app that can be used to stream audio, video, or both. This guide will show how to use the `Stream` object to build a variety of applications.

## Core Concepts

Here's a simple example of creating a video object detection stream. We'll use it to explain the core concepts of the `Stream` object.

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

You can define additional input and output components using the `additional_inputs` and `additional_outputs` arguments. These components will be displayed in the automatically generated Gradio interface (see [Built-in Documentation Routes](#built-in-documentation-routes)).

In our example, we added a slider to the Gradio interface to control the confidence threshold for the object detection model.

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

The `handler` argument is the main component of the `Stream` object. A handler can be one of the following:

- If `modality="video"` and `mode="send-receive"`: A function that receives the latest frame and return the corresponding frame
- If `modality="video"` and `mode="receive"`: A generator that yields the next video frames
- If `modality="audio"` and `mode="receive"`: A generator that yields the next audio frames
- For all other audio cases: A class that inherits from `AsyncStreamHandler` or `StreamHandler`.
- If `modality="audio-video"`: A class that inherits from `AsyncAudioVideoStreamHandler` or `AudioVideoStreamHandler`.

### Built-in Documentation Routes

FastRTC automatically configures several documentation routes for your Stream:

1. `/ui` - Auto-generated Gradio interface for testing your stream.
2. `/webrtc/docs` - Documentation and Gradio UI for WebRTC connections.
3. `/websocket/docs` - Documentation for WebSocket connections
4. `/telephone/docs` - Documentation for telephone integration

## Audio Streaming

### Reply On Pause

Typically, you want to run a python function whenever a user has stopped speaking. This can be done by wrapping a python generator with the `ReplyOnPause` class and passing it to the `handler` argument of the `Stream` object.

```python
from fastrtc import ReplyOnPause, Stream

def response(audio: tuple[int, np.ndarray]): # (1)
    sample_rate, audio_array = audio
    # Generate response
    for audio_chunk in generate_response(sample_rate, audio_array):
        yield (sample_rate, audio_chunk) # (2)

stream = Stream(
    handler=ReplyOnPause(response),
    modality="audio",
    mode="send-receive"
)
```

1. The python generator will receive the **entire** audio up until the user stopped. It will be a tuple of the form (sampling_rate, numpy array of audio). The array will have a shape of (1, num_samples). You can also pass in additional input components.

2. The generator must yield audio chunks as a tuple of (sampling_rate, numpy audio array). Each numpy audio array must have a shape of (1, num_samples).


The `ReplyOnPause` class will handle the voice detection and turn taking logic automatically!

!!! tip "Parameters"
    You can customize the voice detection parameters by passing in `algo_options` and `model_options` to the `ReplyOnPause` class.
    ```python
    from fastrtc import AlgoOptions, SileroVadOptions

    stream = Stream(
        handler=ReplyOnPause(
            response,
            algo_options=AlgoOptions(
                audio_chunk_duration=0.6,
                started_talking_threshold=0.2,
                speech_threshold=0.1
            ),
            model_options=SileroVadOptions(
                threshold=0.5,
                min_speech_duration_ms=250,
                min_silence_duration_ms=100
            )
        )
    )
    ```

### Async Stream Handler

For more complex audio processing, especially when working with async APIs, use `AsyncStreamHandler`:

```python
from fastrtc import AsyncStreamHandler

class MyAudioHandler(AsyncStreamHandler):
    def __init__(self):
        super().__init__(
            expected_layout="mono",
            output_sample_rate=24000,
            output_frame_size=480
        )
        self.queue = asyncio.Queue()

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        sample_rate, audio = frame
        # Process incoming audio
        await self.queue.put(processed_audio)

    async def emit(self) -> tuple[int, np.ndarray] | None:
        return await self.queue.get()

    def copy(self) -> "MyAudioHandler":
        return MyAudioHandler()

stream = Stream(
    handler=MyAudioHandler(),
    modality="audio",
    mode="send-receive"
)
```

## Video Streaming

### Basic Video Handler

For simple video processing:

```python
def process_video(frame: np.ndarray):
    # Process frame
    return processed_frame

stream = Stream(
    handler=process_video,
    modality="video",
    mode="send-receive"
)
```

### Additional Inputs/Outputs

You can add UI components that interact with your stream:

```python
stream = Stream(
    handler=process_video,
    modality="video",
    mode="send-receive",
    additional_inputs=[
        gr.Slider(label="Threshold", minimum=0, maximum=1)
    ],
    additional_outputs=[
        gr.Textbox(label="Detection Results")
    ],
    additional_outputs_handler=lambda results: results
)
```

## Advanced Features

### Additional Outputs During Streaming

To update UI components during streaming:

```python
from fastrtc import AdditionalOutputs

def process_with_updates(frame):
    result = process_frame(frame)
    yield (result, AdditionalOutputs("Detection complete!"))

stream = Stream(
    handler=process_with_updates,
    modality="video",
    additional_outputs=[gr.Textbox()],
    additional_outputs_handler=lambda text: text
)
```

### Custom Input Hooks

To handle custom input updates:

```python
from pydantic import BaseModel

class InputData(BaseModel):
    webrtc_id: str
    threshold: float

@stream.post("/input_hook")
async def update_input(data: InputData):
    stream.set_input(data.webrtc_id, data.threshold)
```

### Server-Sent Events

To stream updates to the client:

```python
@stream.get("/updates")
def stream_updates(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            yield f"data: {output}\n\n"

    return StreamingResponse(
        output_stream(), 
        media_type="text/event-stream"
    )
```

## Best Practices

1. Always implement the `copy()` method in custom handlers
2. Use appropriate sample rates and frame sizes for audio
3. Handle cleanup in async handlers using `shutdown()`
4. Set appropriate concurrency limits for resource management
5. Use error handling in receive/emit methods

## Common Patterns

### Audio Transcription
```python
from fastrtc import ReplyOnPause

def transcribe(audio: tuple[int, np.ndarray]):
    transcript = transcription_model(audio)
    yield AdditionalOutputs(transcript)

stream = Stream(
    ReplyOnPause(transcribe),
    modality="audio",
    mode="send",
    additional_outputs=[gr.Textbox(label="Transcript")]
)
```

### Real-time Video Detection
```python
def detect_objects(frame: np.ndarray, conf_threshold: float):
    detections = model.detect(frame, conf_threshold)
    return annotate_frame(frame, detections)

stream = Stream(
    detect_objects,
    modality="video",
    mode="send-receive",
    additional_inputs=[
        gr.Slider(label="Confidence", value=0.3)
    ]
)
```

For more examples and complete implementations, check out the demo applications in the repository.


## Voice Detection and Turn Taking

FastRTC provides built-in voice activity detection through the `ReplyOnPause` handler:

```python
from fastrtc import ReplyOnPause, Stream

def response(audio: tuple[int, np.ndarray]):
    # Process audio that was captured after user stopped speaking
    for audio_chunk in generated_response:
        yield (sample_rate, audio_chunk)

stream = Stream(
    handler=ReplyOnPause(response),
    modality="audio",
    mode="send-receive"
)
```

You can customize the voice detection parameters:

```python
from fastrtc import AlgoOptions, SileroVadOptions

stream = Stream(
    handler=ReplyOnPause(
        response,
        algo_options=AlgoOptions(
            audio_chunk_duration=0.6,
            started_talking_threshold=0.2,
            speech_threshold=0.1
        ),
        model_options=SileroVadOptions(
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100
        )
    )
)
```

## Custom Routes and Frontend Integration

Since a Stream is just a FastAPI app, you can add custom routes for serving your frontend or handling additional functionality:

```python
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Serve a custom frontend
@stream.get("/")
async def serve_frontend():
    return HTMLResponse(content=open("index.html").read())

# Handle input updates
class InputData(BaseModel):
    webrtc_id: str
    parameter: float

@stream.post("/input_hook")
async def update_input(data: InputData):
    stream.set_input(data.webrtc_id, data.parameter)

# Stream updates to the client
@stream.get("/updates")
def stream_updates(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            yield f"data: {output}\n\n"

    return StreamingResponse(
        output_stream(), 
        media_type="text/event-stream"
    )
```

## Telephone Integration

FastRTC provides built-in telephone support through the `fastphone()` method:

```python
# Launch with a temporary phone number
stream.fastphone(
    token="your_hf_token",  # Optional: HuggingFace token
    host="127.0.0.1",
    port=8000
)
```

This will provide you with a temporary phone number that users can call to interact with your stream.

## Launching Your Stream

There are several ways to launch your FastRTC stream:

### Using uvicorn directly:
```bash
uvicorn app:stream --host 0.0.0.0 --port 8000
```

### Using Python:
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(stream, host="0.0.0.0", port=8000)
```

### With telephone support:
```python
if __name__ == "__main__":
    stream.fastphone(host="0.0.0.0", port=8000)
```

### Development vs Production
For development:
```bash
uvicorn app:stream --reload
```

For production:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:stream
```

## Additional Outputs During Streaming

You can update UI components during streaming using `AdditionalOutputs`:

```python
from fastrtc import AdditionalOutputs

def process_with_updates(audio):
    # Update UI first
    yield AdditionalOutputs({"status": "Processing..."})
    
    # Process audio
    result = process_audio(audio)
    
    # Update UI with result
    yield AdditionalOutputs({"status": "Complete!"})
    
    # Return audio
    yield (sample_rate, result)

stream = Stream(
    handler=process_with_updates,
    modality="audio",
    additional_outputs=[gr.JSON()],
    additional_outputs_handler=lambda status: status
)
```

## Best Practices

1. Always handle cleanup in async handlers:
```python
class MyHandler(AsyncStreamHandler):
    async def shutdown(self) -> None:
        await self.client.close()
        self.reset_state()
```

2. Set appropriate concurrency limits:
```python
stream = Stream(
    handler=my_handler,
    concurrency_limit=10  # Limit concurrent connections
)
```

3. Use error handling in receive/emit methods:
```python
async def receive(self, frame: tuple[int, np.ndarray]) -> None:
    try:
        await self.process_frame(frame)
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
```

4. Reset state between sessions:
```python
def reset_state(self):
    self.connection = None
    self.args_set.clear()
    self.connected.clear()
```