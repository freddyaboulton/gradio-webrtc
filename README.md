<div style='text-align: center; margin-bottom: 1rem; display: flex; justify-content: center; align-items: center;'>
    <h1 style='color: white; margin: 0;'>FastRTC</h1>
    <img src='https://huggingface.co/datasets/freddyaboulton/bucket/resolve/main/fastrtc_logo_small.png'
         alt="FastRTC Logo" 
         style="margin-right: 10px;">
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
pip install fastrtc
```

to use built-in pause detection (see [ReplyOnPause](https://freddyaboulton.github.io/gradio-webrtc//user-guide/#reply-on-pause)), install the `vad` extra:

```bash
pip install fastrtc[vad]
```

For stop word detection (see [ReplyOnStopWords](https://freddyaboulton.github.io/gradio-webrtc//user-guide/#reply-on-stopwords)), install the `stopword` extra:

```bash
pip install fastrtc[stopword]
```

## Docs

https://freddyaboulton.github.io/gradio-webrtc/

## Examples

<table>
<tr>
<td width="50%">
<h3>🗣️ Audio Input/Output with mini-omni2</h3>
<p>Build a GPT-4o like experience with mini-omni2, an audio-native LLM.</p>
<video width="100%" src="https://github.com/user-attachments/assets/58c06523-fc38-4f5f-a4ba-a02a28e7fa9e" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/mini-omni2-webrtc">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/mini-omni2-webrtc/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
<h3>🗣️ Talk to Claude</h3>
<p>Use the Anthropic and Play.Ht APIs to have an audio conversation with Claude.</p>
<video width="100%" src="https://github.com/user-attachments/assets/650bc492-798e-4995-8cef-159e1cfc2185" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-claude">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-claude/blob/main/app.py">Code</a>
</p>
</td>
</tr>

<tr>
<td width="50%">
<h3>🗣️ Kyutai Moshi</h3>
<p>Kyutai's moshi is a novel speech-to-speech model for modeling human conversations.</p>
<video width="100%" src="https://github.com/user-attachments/assets/becc7a13-9e89-4a19-9df2-5fb1467a0137" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-moshi">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-moshi/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
<h3>🗣️ Hello Llama: Stop Word Detection</h3>
<p>A code editor built with Llama 3.3 70b that is triggered by the phrase "Hello Llama". Build a Siri-like coding assistant in 100 lines of code!</p>
<video width="100%" src="https://github.com/user-attachments/assets/3e10cb15-ff1b-4b17-b141-ff0ad852e613" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/hey-llama-code-editor">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/hey-llama-code-editor/blob/main/app.py">Code</a>
</p>
</td>
</tr>

<tr>
<td width="50%">
<h3>🤖 Llama Code Editor</h3>
<p>Create and edit HTML pages with just your voice! Powered by SambaNova systems.</p>
<video width="100%" src="https://github.com/user-attachments/assets/a09647f1-33e1-4154-a5a3-ffefda8a736a" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/llama-code-editor">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/llama-code-editor/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
<h3>🗣️ Talk to Ultravox</h3>
<p>Talk to Fixie.AI's audio-native Ultravox LLM with the transformers library.</p>
<video width="100%" src="https://github.com/user-attachments/assets/e6e62482-518c-4021-9047-9da14cd82be1" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-ultravox">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-ultravox/blob/main/app.py">Code</a>
</p>
</td>
</tr>

<tr>
<td width="50%">
<h3>🗣️ Talk to Llama 3.2 3b</h3>
<p>Use the Lepton API to make Llama 3.2 talk back to you!</p>
<video width="100%" src="https://github.com/user-attachments/assets/3ee37a6b-0892-45f5-b801-73188fdfad9a" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/llama-3.2-3b-voice-webrtc">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/llama-3.2-3b-voice-webrtc/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
<h3>🤖 Talk to Qwen2-Audio</h3>
<p>Qwen2-Audio is a SOTA audio-to-text LLM developed by Alibaba.</p>
<video width="100%" src="https://github.com/user-attachments/assets/c821ad86-44cc-4d0c-8dc4-8c02ad1e5dc8" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-qwen-webrtc">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/talk-to-qwen-webrtc/blob/main/app.py">Code</a>
</p>
</td>
</tr>

<tr>
<td width="50%">
<h3>📷 Yolov10 Object Detection</h3>
<p>Run the Yolov10 model on a user webcam stream in real time!</p>
<video width="100%" src="https://github.com/user-attachments/assets/c90d8c9d-d2d5-462e-9e9b-af969f2ea73c" controls></video>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/webrtc-yolov10n">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/webrtc-yolov10n/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
<h3>📷 Video Object Detection with RT-DETR</h3>
<p>Upload a video and stream out frames with detected objects (powered by RT-DETR) model.</p>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/rt-detr-object-detection-webrtc">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/rt-detr-object-detection-webrtc/blob/main/app.py">Code</a>
</p>
</td>
</tr>

<tr>
<td width="50%">
<h3>🔊 Text-to-Speech with Parler</h3>
<p>Stream out audio generated by Parler TTS!</p>
<p>
<a href="https://huggingface.co/spaces/freddyaboulton/parler-tts-streaming-webrtc">Demo</a> |
<a href="https://huggingface.co/spaces/freddyaboulton/parler-tts-streaming-webrtc/blob/main/app.py">Code</a>
</p>
</td>
<td width="50%">
</td>
</tr>
</table>

## Usage

This is an shortened version of the official [usage guide](https://freddyaboulton.github.io/gradio-webrtc/user-guide/). 

To get started with WebRTC streams, all that's needed is to import the `WebRTC` component from this package and implement its `stream` event. 

### Reply on Pause

Typically, you want to run an AI model that generates audio when the user has stopped speaking. This can be done by wrapping a python generator with the `ReplyOnPause` class
and passing it to the `stream` event of the `WebRTC` component.

```py 
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


### Reply On Stopwords

You can configure your AI model to run whenever a set of "stop words" are detected, like "Hey Siri" or "computer", with the `ReplyOnStopWords` class. 

The API is similar to `ReplyOnPause` with the addition of a `stop_words` parameter.


```py 
import gradio as gr
from gradio_webrtc import WebRTC, ReplyOnPause

def response(audio: tuple[int, np.ndarray]):
    """This function must yield audio frames"""
    ...
    for numpy_array in generated_audio:
        yield (sampling_rate, numpy_array, "mono")


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
                mode="send",
                modality="audio",
            )
    webrtc.stream(ReplyOnStopWords(generate,
                            input_sample_rate=16000,
                            stop_words=["computer"]), # (1)
                    inputs=[webrtc, history, code],
                    outputs=[webrtc], time_limit=90,
                    concurrency_limit=10)

demo.launch()
```

1. The `stop_words` can be single words or pairs of words. Be sure to include common misspellings of your word for more robust detection, e.g. "llama", "lamma". In my experience, it's best to use two very distinct words like "ok computer" or "hello iris". 
    

### Audio Server-To-Clien

To stream only from the server to the client, implement a python generator and pass it to the component's `stream` event. The stream event must also specify a `trigger` corresponding to a UI interaction that starts the stream. In this case, it's a button click.



```py
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


### Video Input/Output Streaming
Set up a video Input/Output stream to continuosly receive webcam frames from the user and run an arbitrary python function to return a modified frame.
    
```py
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

### Server-to-Client Only

Set up a server-to-client stream to stream video from an arbitrary user interaction.

```py 
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


### Additional Outputs

In order to modify other components from within the WebRTC stream, you must yield an instance of `AdditionalOutputs` and add an `on_additional_outputs` event to the `WebRTC` component.

This is common for displaying a multimodal text/audio conversation in a Chatbot UI.



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


## Deployment

When deploying in a cloud environment (like Hugging Face Spaces, EC2, etc), you need to set up a TURN server to relay the WebRTC traffic.
The easiest way to do this is to use a service like Twilio.

```python
from twilio.rest import Client
import os

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

token = client.tokens.create()

rtc_configuration = {
    "iceServers": token.ice_servers,
    "iceTransportPolicy": "relay",
}

with gr.Blocks() as demo:
    ...
    rtc = WebRTC(rtc_configuration=rtc_configuration, ...)
    ...
```