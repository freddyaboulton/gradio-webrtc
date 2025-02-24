# Gradio Component

The automatic gradio UI is a great way to test your stream. However, you may want to customize the UI to your liking or simply build a standalone Gradio application. 

## The WebRTC Component

To build a standalone Gradio application, you can use the `WebRTC` component and implement the `stream` event.
Similarly to the `Stream` object, you must set the `mode` and `modality` arguments and pass in a `handler`.

Below are some common examples of how to use the `WebRTC` component.


=== "Reply On Pause"
    ``` py
    import gradio as gr
    from gradio_webrtc import WebRTC, ReplyOnPause

    def response(audio: tuple[int, np.ndarray]): # (1)
        """This function must yield audio frames"""
        ...
        for numpy_array in generated_audio:
            yield (sampling_rate, numpy_array, "mono") # (2)


    with gr.Blocks() as demo:
        gr.HTML(
        """
        <h1 style='text-align: center'>
        Chat (Powered by WebRTC ⚡️)
        </h1>
        """
        )
        with gr.Column():
            with gr.Group():
                audio = WebRTC(
                    mode="send-receive", # (3)
                    modality="audio",
                )
            audio.stream(fn=ReplyOnPause(response),
                        inputs=[audio], outputs=[audio], # (4)
                        time_limit=60) # (5)

    demo.launch()
    ```

    1. The python generator will receive the **entire** audio up until the user stopped. It will be a tuple of the form (sampling_rate, numpy array of audio). The array will have a shape of (1, num_samples). You can also pass in additional input components.

    2. The generator must yield audio chunks as a tuple of (sampling_rate, numpy audio array). Each numpy audio array must have a shape of (1, num_samples).

    3. The `mode` and `modality` arguments must be set to `"send-receive"` and `"audio"`.

    4. The `WebRTC` component must be the first input and output component. 

    5. Set a `time_limit` to control how long a conversation will last. If the `concurrency_count` is 1 (default), only one conversation will be handled at a time.

=== "AsyncStreamHandler"
    ``` py

    import asyncio
    import base64
    import logging
    import os

    import gradio as gr
    import numpy as np
    from google import genai
    from gradio_webrtc import (
        AsyncStreamHandler,
        WebRTC,
        async_aggregate_bytes_to_16bit,
        get_twilio_turn_credentials,
    )

    class GeminiHandler(AsyncStreamHandler):
        def __init__(
            self, expected_layout="mono", output_sample_rate=24000, output_frame_size=480
        ) -> None:
            super().__init__(
                expected_layout,
                output_sample_rate,
                output_frame_size,
                input_sample_rate=16000,
            )
            self.client: genai.Client | None = None
            self.input_queue = asyncio.Queue()
            self.output_queue = asyncio.Queue()
            self.quit = asyncio.Event()
            self.connected = asyncio.Event()

        def copy(self) -> "GeminiHandler":
            return GeminiHandler(
                expected_layout=self.expected_layout,
                output_sample_rate=self.output_sample_rate,
                output_frame_size=self.output_frame_size,
            )

        async def stream(self):
            while not self.quit.is_set():
                audio = await self.input_queue.get()
                yield audio

        async def connect(self, api_key: str):
            client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
            config = {"response_modalities": ["AUDIO"]}
            async with client.aio.live.connect(
                model="gemini-2.0-flash-exp", config=config
            ) as session:
                self.connected.set()
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

        async def generator(self):
            async for audio_response in async_aggregate_bytes_to_16bit(
                self.connect(api_key=self.latest_args[1])
            ):
                self.output_queue.put_nowait(audio_response)

        async def emit(self):
            if not self.args_set.is_set():
                await self.wait_for_args()
            
            if not self.connected.is_set():
                asyncio.create_task(self.generator())
                await self.connected.wait()

            array = await self.output_queue.get()
            return (self.output_sample_rate, array)

        def shutdown(self) -> None:
            self.quit.set()

    with gr.Blocks() as demo:
        gr.HTML(
            """
            <div style='text-align: center'>
                <h1>Gen AI SDK Voice Chat</h1>
                <p>Speak with Gemini using real-time audio streaming</p>
                <p>Get an API Key <a href="https://support.google.com/googleapi/answer/6158862?hl=en">here</a></p>
            </div>
        """
        )
        with gr.Row() as api_key_row:
            api_key = gr.Textbox(
                label="API Key",
                placeholder="Enter your API Key",
                value=os.getenv("GOOGLE_API_KEY", ""),
                type="password",
            )
        with gr.Row(visible=False) as row:
            webrtc = WebRTC(
                label="Audio",
                modality="audio",
                mode="send-receive",
                rtc_configuration=get_twilio_turn_credentials(),
                pulse_color="rgb(35, 157, 225)",
                icon_button_color="rgb(35, 157, 225)",
                icon="https://www.gstatic.com/lamda/images/gemini_favicon_f069958c85030456e93de685481c559f160ea06b.png",
            )

        webrtc.stream(
            GeminiHandler(),
            inputs=[webrtc, api_key],
            outputs=[webrtc],
            time_limit=90,
            concurrency_limit=2,
        )
        api_key.submit(
            lambda: (gr.update(visible=False), gr.update(visible=True)),
            None,
            [api_key_row, row],
        )    
    ```
=== "Server-To-Client Audio"

    ``` py
    import gradio as gr
    from gradio_webrtc import WebRTC
    from pydub import AudioSegment

    def generation(num_steps):
        for _ in range(num_steps):
            segment = AudioSegment.from_file("audio_file.wav")
            array = np.array(segment.get_array_of_samples()).reshape(1, -1)
            yield (segment.frame_rate, array)

    with gr.Blocks() as demo:
        audio = WebRTC(label="Stream", mode="receive",  # (1)
                       modality="audio")
        num_steps = gr.Slider(label="Number of Steps", minimum=1,
                              maximum=10, step=1, value=5)
        button = gr.Button("Generate")

        audio.stream(
            fn=generation, inputs=[num_steps], outputs=[audio],
            trigger=button.click # (2)
        )
    ```

    1. Set `mode="receive"` to only receive audio from the server.
    2. The `stream` event must take a `trigger` that corresponds to the gradio event that starts the stream. In this case, it's the button click.

=== "Video Streaming"
    
    ``` py
    import gradio as gr
    from gradio_webrtc import WebRTC


    def detection(image, conf_threshold=0.3): # (1)
        ... your detection code here ...
        return modified_frame # (2)


    with gr.Blocks() as demo:
        image = WebRTC(label="Stream", mode="send-receive", modality="video") # (3)
        conf_threshold = gr.Slider(
            label="Confidence Threshold",
            minimum=0.0,
            maximum=1.0,
            step=0.05,
            value=0.30,
        )
        image.stream(
            fn=detection,
            inputs=[image, conf_threshold], # (4)
            outputs=[image], time_limit=10
        )

    if __name__ == "__main__":
        demo.launch()
    ```

    1. The webcam frame will be represented as a numpy array of shape (height, width, RGB).
    2. The function must return a numpy array. It can take arbitrary values from other components.
    3. Set the `modality="video"` and `mode="send-receive"`
    4. The `inputs` parameter should be a list where the first element is the WebRTC component. The only output allowed is the WebRTC component.

=== "Server-To-Client Video"
    ``` py
        import gradio as gr
        from gradio_webrtc import WebRTC
        import cv2

        def generation():
            url = "https://download.tsi.telecom-paristech.fr/gpac/dataset/dash/uhd/mux_sources/hevcds_720p30_2M.mp4"
            cap = cv2.VideoCapture(url)
            iterating = True
            while iterating:
                iterating, frame = cap.read()
                yield frame # (1)

        with gr.Blocks() as demo:
            output_video = WebRTC(label="Video Stream", mode="receive", # (2)
                                  modality="video")
            button = gr.Button("Start", variant="primary")
            output_video.stream(
                fn=generation, inputs=None, outputs=[output_video],
                trigger=button.click # (3)
            )
            demo.launch()
    ```

    1. The `stream` event's `fn` parameter is a generator function that yields the next frame from the video as a **numpy array**.
    2. Set `mode="receive"` to only receive audio from the server.
    3. The `trigger` parameter the gradio event that will trigger the stream. In this case, the button click event.

!!! tip
    You can configure the `time_limit` and `concurrency_limit` parameters of the `stream` event similar to the `Stream` object.

## Additional Outputs

In order to modify other components from within the WebRTC stream, you must yield an instance of `AdditionalOutputs` and add an `on_additional_outputs` event to the `WebRTC` component.

This is common for displaying a multimodal text/audio conversation in a Chatbot UI.

=== "Code"

    ``` py title="Additional Outputs"
    from gradio_webrtc import AdditionalOutputs, WebRTC

    def transcribe(audio: tuple[int, np.ndarray],
                   transformers_convo: list[dict],
                   gradio_convo: list[dict]):
        response = model.generate(**inputs, max_length=256)
        transformers_convo.append({"role": "assistant", "content": response})
        gradio_convo.append({"role": "assistant", "content": response})
        yield AdditionalOutputs(transformers_convo, gradio_convo) # (1)


    with gr.Blocks() as demo:
        gr.HTML(
        """
        <h1 style='text-align: center'>
        Talk to Qwen2Audio (Powered by WebRTC ⚡️)
        </h1>
        """
        )
        transformers_convo = gr.State(value=[])
        with gr.Row():
            with gr.Column():
                audio = WebRTC(
                    label="Stream",
                    mode="send", # (2)
                    modality="audio",
                )
            with gr.Column():
                transcript = gr.Chatbot(label="transcript", type="messages")

        audio.stream(ReplyOnPause(transcribe),
                    inputs=[audio, transformers_convo, transcript],
                    outputs=[audio], time_limit=90)
        audio.on_additional_outputs(lambda s,a: (s,a), # (3)
                                    outputs=[transformers_convo, transcript],
                                    queue=False, show_progress="hidden")
        demo.launch()
    ```
    
    1. Pass your data to `AdditionalOutputs` and yield it.
    2. In this case, no audio is being returned, so we set `mode="send"`. However, if we set `mode="send-receive"`, we could also yield generated audio and `AdditionalOutputs`.
    3. The `on_additional_outputs` event does not take `inputs`. It's common practice to not run this event on the queue since it is just a quick UI update.
=== "Notes"
    1. Pass your data to `AdditionalOutputs` and yield it.
    2. In this case, no audio is being returned, so we set `mode="send"`. However, if we set `mode="send-receive"`, we could also yield generated audio and `AdditionalOutputs`.
    3. The `on_additional_outputs` event does not take `inputs`. It's common practice to not run this event on the queue since it is just a quick UI update.