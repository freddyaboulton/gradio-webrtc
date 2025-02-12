# Audio Streaming

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

    stream = Stream(
        handler=EchoHandler(),
        modality="audio",
        mode="send-receive"
    )
    ```

    1. The `StreamHandler` class implements three methods: `receive`, `emit` and `copy`. The `receive` method is called when a new frame is received from the client, and the `emit` method returns the next frame to send to the client. The `copy` method is called at the beginning of the stream to ensure each user has a unique stream handler.
    2. The `emit` method SHOULD NOT block. If a frame is not ready to be sent, the method should return `None`.
    3. The `shutdown` method is called when the stream is closed. It should be used to clean up any resources.
=== "Notes"
    1. The `StreamHandler` class implements three methods: `receive`, `emit` and `copy`. The `receive` method is called when a new frame is received from the client, and the `emit` method returns the next frame to send to the client. The `copy` method is called at the beginning of the stream to ensure each user has a unique stream handler.
    2. The `emit` method SHOULD NOT block. If a frame is not ready to be sent, the method should return `None`.
    3. The `shutdown` method is called when the stream is closed. It should be used to clean up any resources.

!!! tip
    See this [demo](https://github.com/fastrtc/fastrtc/blob/main/examples/echo_handler.py) for a complete example of a more complex stream handler.

## Async Stream Handlers

It is also possible to create asynchronous stream handlers. This is very convenient for accessing async APIs from major LLM developers, like Google and OpenAI. The main difference is that `receive` and `emit` are now defined with `async def`.

Here is a complete example of using `AsyncStreamHandler` for using the Google Gemini real time API:

=== "Code"
    ``` py

    from fastrtc import AsyncStreamHandler
    import asyncio
    import base64
    import os
    import google.generativeai as genai
    from google.generativeai.types import (
        LiveConnectConfig, SpeechConfig, 
        VoiceConfig, PrebuiltVoiceConfig
    )

    class GeminiHandler(AsyncStreamHandler):
        """Handler for the Gemini API"""

        def __init__(
            self,
            expected_layout: Literal["mono"] = "mono",
            output_sample_rate: int = 24000,
            output_frame_size: int = 480,
        ) -> None:
            super().__init__(
                expected_layout,
                output_sample_rate,
                output_frame_size,
                input_sample_rate=16000,
            )
            self.input_queue: asyncio.Queue = asyncio.Queue()
            self.output_queue: asyncio.Queue = asyncio.Queue()
            self.quit: asyncio.Event = asyncio.Event()

        def copy(self) -> "GeminiHandler":
            return GeminiHandler(
                expected_layout="mono",
                output_sample_rate=self.output_sample_rate,
                output_frame_size=self.output_frame_size,
            )

        async def stream(self) -> AsyncGenerator[bytes, None]:
            while not self.quit.is_set():
                audio = await self.input_queue.get()
                yield audio
            return

        async def connect(
            self, api_key: str | None = None, voice_name: str | None = None
        ) -> AsyncGenerator[bytes, None]:
            """Connect to to genai server and start the stream"""
            client = genai.Client(
                api_key=api_key or os.getenv("GEMINI_API_KEY"),
                http_options={"api_version": "v1alpha"},
            )
            config = LiveConnectConfig(
                response_modalities=["AUDIO"],  # type: ignore
                speech_config=SpeechConfig(
                    voice_config=VoiceConfig(
                        prebuilt_voice_config=PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                ),
            )
            async with client.aio.live.connect(
                model="gemini-2.0-flash-exp", config=config
            ) as session:
                async for audio in session.start_stream(
                    stream=self.stream(), mime_type="audio/pcm"
                ):
                    if audio.data:
                        yield audio.data

        async def receive(self, frame: tuple[int, np.ndarray]) -> None:
            _, array = frame
            array = array.squeeze()
            audio_message = base64.b64encode(array.tobytes()).decode("UTF-8")
            self.input_queue.put_nowait(audio_message)

        async def generator(self) -> None:
            async for audio_response in async_aggregate_bytes_to_16bit(
                self.connect(*self.latest_args[1:])
            ):
                self.output_queue.put_nowait(audio_response)

        async def emit(self) -> tuple[int, np.ndarray]:
            if not self.args_set.is_set():
                await self.wait_for_args()
                asyncio.create_task(self.generator())

            array = await self.output_queue.get()
            return (self.output_sample_rate, array)

        def shutdown(self) -> None:
            self.quit.set()
            self.args_set.clear()
            self.quit.clear()
    ```

## Requesting Inputs

In `ReplyOnPause` and `ReplyOnStopWords`, any additional input data is automatically passed to your generator. For `StreamHandler`s, you must manually request the input data from the client.

You can do this by calling `await self.wait_for_args()` (for `AsyncStreamHandler`s) in either the `emit` or `receive` methods. For a `StreamHandler`, you can call `self.wait_for_args_sync()`.


We can access the value of this component via the `latest_args` property of the `StreamHandler`. The `latest_args` is a list storing each of the values. The 0th index is the dummy string `__webrtc_value__`.