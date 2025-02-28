
## Reply On Pause

Typically, you want to run a python function whenever a user has stopped speaking. This can be done by wrapping a python generator with the `ReplyOnPause` class and passing it to the `handler` argument of the `Stream` object.

=== "Code"
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

=== "Notes"
    1. The python generator will receive the **entire** audio up until the user stopped. It will be a tuple of the form (sampling_rate, numpy array of audio). The array will have a shape of (1, num_samples). You can also pass in additional input components.

    2. The generator must yield audio chunks as a tuple of (sampling_rate, numpy audio array). Each numpy audio array must have a shape of (1, num_samples).


The `ReplyOnPause` class will handle the voice detection and turn taking logic automatically!

!!! warning "Argument Order"

    The first argument to the function must be the audio

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

## Reply On Stopwords

You can configure your AI model to run whenever a set of "stop words" are detected, like "Hey Siri" or "computer", with the `ReplyOnStopWords` class. 

The API is similar to `ReplyOnPause` with the addition of a `stop_words` parameter.

=== "Code"
    ``` py
    from fastrtc import Stream, ReplyOnStopWords

    def response(audio: tuple[int, np.ndarray]):
        """This function must yield audio frames"""
        ...
        for numpy_array in generated_audio:
            yield (sampling_rate, numpy_array, "mono")

    stream = Stream(
        handler=ReplyOnStopWords(generate,
                                input_sample_rate=16000,
                                stop_words=["computer"]), # (1)
        modality="audio",
        mode="send-receive"
    )
    ```

    1. The `stop_words` can be single words or pairs of words. Be sure to include common misspellings of your word for more robust detection, e.g. "llama", "lamma". In my experience, it's best to use two very distinct words like "ok computer" or "hello iris". 
    
=== "Notes"
    1. The `stop_words` can be single words or pairs of words. Be sure to include common misspellings of your word for more robust detection, e.g. "llama", "lamma". In my experience, it's best to use two very distinct words like "ok computer" or "hello iris". 

!!! tip "Extra Dependencies"
    The `ReplyOnStopWords` class requires the the `stopword` extra. Run `pip install fastrtc[stopword]` to install it.

!!! warning "English Only"
    The `ReplyOnStopWords` class is currently only supported for English.

## Stream Handler

`ReplyOnPause` and `ReplyOnStopWords` are implementations of a `StreamHandler`. The `StreamHandler` is a low-level abstraction that gives you arbitrary control over how the input audio stream and output audio stream are created. The following example echos back the user audio.

=== "Code"
    ``` py
    import gradio as gr
    from gradio_webrtc import WebRTC, StreamHandler
    from queue import Queue

    class EchoHandler(StreamHandler):
        def __init__(self) -> None:
            super().__init__()
            self.queue = Queue()

        def receive(self, frame: tuple[int, np.ndarray]) -> None: # (1)
            self.queue.put(frame)

        def emit(self) -> None: # (2)
            return self.queue.get()
        
        def copy(self) -> StreamHandler:
            return EchoHandler()
        
        def shutdown(self) -> None: # (3)
            pass
        
        def start_up(self) -> None: # (4)
            pass

    stream = Stream(
        handler=EchoHandler(),
        modality="audio",
        mode="send-receive"
    )
    ```

    1. The `StreamHandler` class implements three methods: `receive`, `emit` and `copy`. The `receive` method is called when a new frame is received from the client, and the `emit` method returns the next frame to send to the client. The `copy` method is called at the beginning of the stream to ensure each user has a unique stream handler.
    2. The `emit` method SHOULD NOT block. If a frame is not ready to be sent, the method should return `None`. If you need to wait for a frame, use [`wait_for_item`](../../utils#wait_for_item) from the `utils` module.
    3. The `shutdown` method is called when the stream is closed. It should be used to clean up any resources.
    4. The `start_up` method is called when the stream is first created. It should be used to initialize any resources. See [Talk To OpenAI](https://huggingface.co/spaces/fastrtc/talk-to-openai-gradio) or [Talk To Gemini](https://huggingface.co/spaces/fastrtc/talk-to-gemini-gradio) for an example of a `StreamHandler` that uses the `start_up` method to connect to an API.    
=== "Notes"
    1. The `StreamHandler` class implements three methods: `receive`, `emit` and `copy`. The `receive` method is called when a new frame is received from the client, and the `emit` method returns the next frame to send to the client. The `copy` method is called at the beginning of the stream to ensure each user has a unique stream handler.
    2. The `emit` method SHOULD NOT block. If a frame is not ready to be sent, the method should return `None`. If you need to wait for a frame, use [`wait_for_item`](../../utils#wait_for_item) from the `utils` module.
    3. The `shutdown` method is called when the stream is closed. It should be used to clean up any resources.
    4. The `start_up` method is called when the stream is first created. It should be used to initialize any resources. See [Talk To OpenAI](https://huggingface.co/spaces/fastrtc/talk-to-openai-gradio) or [Talk To Gemini](https://huggingface.co/spaces/fastrtc/talk-to-gemini-gradio) for an example of a `StreamHandler` that uses the `start_up` method to connect to an API.

!!! tip
    See this [Talk To Gemini](https://huggingface.co/spaces/fastrtc/talk-to-gemini-gradio) for a complete example of a more complex stream handler.

!!! warning
    The `emit` method should not block. If you need to wait for a frame, use [`wait_for_item`](../../utils#wait_for_item) from the `utils` module.

## Async Stream Handlers

It is also possible to create asynchronous stream handlers. This is very convenient for accessing async APIs from major LLM developers, like Google and OpenAI. The main difference is that `receive`, `emit`, and `start_up` are now defined with `async def`.

Here is aa simple example of using `AsyncStreamHandler`:

=== "Code"
    ``` py

    from fastrtc import AsyncStreamHandler, wait_for_item
    import asyncio

    class AsyncEchoHandler(AsyncStreamHandler):
        """Handler for the Gemini API"""
        
        def __init__(self) -> None:
            super().__init__()
            self.queue = asyncio.Queue()

        async def receive(self, frame: tuple[int, np.ndarray]) -> None: 
            self.queue.put(frame)

        async def emit(self) -> None: # (2)
            return await wait_for_item(self.queue)
        
        def copy(self):
            return AsyncEchoHandler()
        
        async def shutdown(self): # (3)
            pass
        
        def start_up(self) -> None: # (4)
            pass
    ```

!!! tip
    See [Talk To Gemini](https://huggingface.co/spaces/fastrtc/talk-to-gemini), [Talk To Openai](https://huggingface.co/spaces/fastrtc/talk-to-openai) for complete examples of `AsyncStreamHandler`s.


## Text To Speech

You can use an on-device text to speech model if you have the `tts` extra installed.
Import the `get_tts_model` function and call it with the model name you want to use.
At the moment, the only model supported is `kokoro`.

The `get_tts_model` function returns an object with three methods:

- `tts`: Synchronous text to speech.
- `stream_tts_sync`: Synchronous text to speech streaming.
- `stream_tts`: Asynchronous text to speech streaming.

```python
from fastrtc import get_tts_model

model = get_tts_model(model="kokoro")

for audio in model.stream_tts_sync("Hello, world!"):
    yield audio

async for audio in model.stream_tts("Hello, world!"):
    yield audio

audio = model.tts("Hello, world!")
```

!!! tip
    You can customize the audio by passing in an instace of `KokoroTTSOptions` to the method.
    See [here](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) for a list of available voices.
    ```python
    from fastrtc import KokoroTTSOptions, get_tts_model

    model = get_tts_model(model="kokoro")

    options = KokoroTTSOptions(
        voice="af_heart",
        speed=1.0,
        lang="en-us"
    )

    audio = model.tts("Hello, world!", options=options)
    ```

## Speech To Text

You can use an on-device speech to text model if you have the `stt` or `stopword` extra installed.
Import the `get_stt_model` function and call it with the model name you want to use.
At the moment, the only models supported are `moonshine/base` and `moonshine/tiny`.

The `get_stt_model` function returns an object with the following method:

- `stt`: Synchronous speech to text.

```python
from fastrtc import get_stt_model

model = get_stt_model(model="moonshine/base")

audio = (16000, np.random.randint(-32768, 32768, size=(1, 16000)))
text = model.stt(audio)
```

!!! tip "Example"
    See [LLM Voice Chat](https://huggingface.co/spaces/fastrtc/llm-voice-chat) for an example of using the `stt` method in a `ReplyOnPause` handler.

!!! warning "English Only"
    The `stt` model is currently only supported for English.

## Requesting Inputs

In `ReplyOnPause` and `ReplyOnStopWords`, any additional input data is automatically passed to your generator. For `StreamHandler`s, you must manually request the input data from the client.

You can do this by calling `await self.wait_for_args()` (for `AsyncStreamHandler`s) in either the `emit` or `receive` methods. For a `StreamHandler`, you can call `self.wait_for_args_sync()`.


We can access the value of this component via the `latest_args` property of the `StreamHandler`. The `latest_args` is a list storing each of the values. The 0th index is the dummy string `__webrtc_value__`.

## Telephone Integration

In order for your handler to work over the phone, you must make sure that your handler is not expecting any additional input data besides the audio.

If you call `await self.wait_for_args()` your stream will wait forever for the additional input data.

The stream handlers have a `phone_mode` property that is set to `True` if the stream is running over the phone. You can use this property to determine if you should wait for additional input data.

```python
def emit(self):
    if self.phone_mode:
        self.latest_args = [None]
    else:
        await self.wait_for_args()
```

### `ReplyOnPause`

The generator you pass to `ReplyOnPause` must have default arguments for all arguments except audio.

If you yield `AdditionalOutputs`, they will be passed in as the input arguments to the generator the next time it is called.

!!! tip
    See [Talk To Claude](https://huggingface.co/spaces/fastrtc/talk-to-claude) for an example of a `ReplyOnPause` handler that is compatible with telephone usage. Notice how the input chatbot history is yielded as an `AdditionalOutput` on each invocation.