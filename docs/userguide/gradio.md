# Gradio Component

The automatic gradio UI is a great way to test your stream. However, you may want to customize the UI to your liking or simply build a standalone Gradio application. 

## The WebRTC Component

To build a standalone Gradio application, you can use the `WebRTC` component and implement the `stream` event.
Similarly to the `Stream` object, you must set the `mode` and `modality` arguments and pass in a `handler`.

In the `stream` event, you pass in your handler as well as the input and output components.

``` py
import gradio as gr
from fastrtc import WebRTC, ReplyOnPause

def response(audio: tuple[int, np.ndarray]):
    """This function must yield audio frames"""
    ...
    yield audio


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
                mode="send-receive",
                modality="audio",
            )
        audio.stream(fn=ReplyOnPause(response),
                    inputs=[audio], outputs=[audio],
                    time_limit=60)
demo.launch()
```

## Additional Outputs

In order to modify other components from within the WebRTC stream, you must yield an instance of `AdditionalOutputs` and add an `on_additional_outputs` event to the `WebRTC` component.

This is common for displaying a multimodal text/audio conversation in a Chatbot UI.

=== "Code"

    ``` py title="Additional Outputs"
    from fastrtc import AdditionalOutputs, WebRTC

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