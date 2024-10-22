import os

import gradio as gr

_docs = {
    "WebRTC": {
        "description": "Stream audio/video with WebRTC",
        "members": {
            "__init__": {
                "rtc_configuration": {
                    "type": "dict[str, Any] | None",
                    "default": "None",
                    "description": "The configration dictionary to pass to the RTCPeerConnection constructor. If None, the default configuration is used.",
                },
                "height": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "The height of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.",
                },
                "width": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "The width of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.",
                },
                "label": {
                    "type": "str | None",
                    "default": "None",
                    "description": "the label for this component. Appears above the component and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component is assigned to.",
                },
                "show_label": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will display label.",
                },
                "container": {
                    "type": "bool",
                    "default": "True",
                    "description": "if True, will place the component in a container - providing some extra padding around the border.",
                },
                "scale": {
                    "type": "int | None",
                    "default": "None",
                    "description": "relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.",
                },
                "min_width": {
                    "type": "int",
                    "default": "160",
                    "description": "minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.",
                },
                "interactive": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will allow users to upload a video; if False, can only be used to display videos. If not provided, this is inferred based on whether the component is used as an input or output.",
                },
                "visible": {
                    "type": "bool",
                    "default": "True",
                    "description": "if False, component will be hidden.",
                },
                "elem_id": {
                    "type": "str | None",
                    "default": "None",
                    "description": "an optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.",
                },
                "elem_classes": {
                    "type": "list[str] | str | None",
                    "default": "None",
                    "description": "an optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.",
                },
                "render": {
                    "type": "bool",
                    "default": "True",
                    "description": "if False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.",
                },
                "key": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "if assigned, will be used to assume identity across a re-render. Components that have the same key across a re-render will have their value preserved.",
                },
                "mirror_webcam": {
                    "type": "bool",
                    "default": "True",
                    "description": "if True webcam will be mirrored. Default is True.",
                },
            },
            "events": {"tick": {"type": None, "default": None, "description": ""}},
        },
        "__meta__": {"additional_interfaces": {}, "user_fn_refs": {"WebRTC": []}},
    }
}


abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css_paths=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
        """
<h1 style='text-align: center; margin-bottom: 1rem'> Gradio WebRTC ⚡️ </h1>

<div style="display: flex; flex-direction: row; justify-content: center">
<img style="display: block; padding-right: 5px; height: 20px;" alt="Static Badge" src="https://img.shields.io/badge/version%20-%200.0.5%20-%20orange"> 
<a href="https://github.com/freddyaboulton/gradio-webrtc" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/github-white?logo=github&logoColor=black"></a>
</div>
""",
        elem_classes=["md-custom"],
        header_links=True,
    )
    gr.Markdown(
        """
## Installation

```bash
pip install gradio_webrtc
```

## Examples:
1. [Object Detection from Webcam with YOLOv10](https://huggingface.co/spaces/freddyaboulton/webrtc-yolov10n) 📷
2. [Streaming Object Detection from Video with RT-DETR](https://huggingface.co/spaces/freddyaboulton/rt-detr-object-detection-webrtc) 🎥
3. [Text-to-Speech](https://huggingface.co/spaces/freddyaboulton/parler-tts-streaming-webrtc) 🗣️

## Usage

The WebRTC component supports the following three use cases:
1. Streaming video from the user webcam to the server and back
2. Streaming Video from the server to the client
3. Streaming Audio from the server to the client

Streaming Audio from client to the server and back (conversational AI) is not supported yet.


## Streaming Video from the User Webcam to the Server and Back

```python
import gradio as gr
from gradio_webrtc import WebRTC


def detection(image, conf_threshold=0.3):
    ... your detection code here ...


with gr.Blocks() as demo:
    image = WebRTC(label="Stream", mode="send-receive", modality="video")
    conf_threshold = gr.Slider(
        label="Confidence Threshold",
        minimum=0.0,
        maximum=1.0,
        step=0.05,
        value=0.30,
    )
    image.stream(
        fn=detection,
        inputs=[image, conf_threshold],
        outputs=[image], time_limit=10
    )

if __name__ == "__main__":
    demo.launch()

```
* Set the `mode` parameter to `send-receive` and `modality` to "video".
* The `stream` event's `fn` parameter is a function that receives the next frame from the webcam 
as a **numpy array** and returns the processed frame also as a **numpy array**.
* Numpy arrays are in (height, width, 3) format where the color channels are in RGB format.
* The `inputs` parameter should be a list where the first element is the WebRTC component. The only output allowed is the WebRTC component.
* The `time_limit` parameter is the maximum time in seconds the video stream will run. If the time limit is reached, the video stream will stop.

## Streaming Video from the User Webcam to the Server and Back

```python
import gradio as gr
from gradio_webrtc import WebRTC
import cv2

def generation():
    url = "https://download.tsi.telecom-paristech.fr/gpac/dataset/dash/uhd/mux_sources/hevcds_720p30_2M.mp4"
    cap = cv2.VideoCapture(url)
    iterating = True
    while iterating:
        iterating, frame = cap.read()
        yield frame

with gr.Blocks() as demo:
    output_video = WebRTC(label="Video Stream", mode="receive", modality="video")
    button = gr.Button("Start", variant="primary")
    output_video.stream(
        fn=generation, inputs=None, outputs=[output_video],
        trigger=button.click
    )

if __name__ == "__main__":
    demo.launch()
```

* Set the "mode" parameter to "receive" and "modality" to "video".
* The `stream` event's `fn` parameter is a generator function that yields the next frame from the video as a **numpy array**.
* The only output allowed is the WebRTC component.
* The `trigger` parameter the gradio event that will trigger the webrtc connection. In this case, the button click event.

## Streaming Audio from the Server to the Client

```python
import gradio as gr
from pydub import AudioSegment

def generation(num_steps):
    for _ in range(num_steps):
        segment = AudioSegment.from_file("/Users/freddy/sources/gradio/demo/audio_debugger/cantina.wav")
        yield (segment.frame_rate, np.array(segment.get_array_of_samples()).reshape(1, -1))

with gr.Blocks() as demo:
    audio = WebRTC(label="Stream", mode="receive", modality="audio")
    num_steps = gr.Slider(
        label="Number of Steps",
        minimum=1,
        maximum=10,
        step=1,
        value=5,
    )
    button = gr.Button("Generate")

    audio.stream(
        fn=generation, inputs=[num_steps], outputs=[audio],
        trigger=button.click
    )
```

* Set the "mode" parameter to "receive" and "modality" to "audio".
* The `stream` event's `fn` parameter is a generator function that yields the next audio segment as a tuple of (frame_rate, audio_samples).
* The numpy array should be of shape (1, num_samples).
* The `outputs` parameter should be a list with the WebRTC component as the only element.

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
""",
        elem_classes=["md-custom"],
        header_links=True,
    )

    gr.Markdown(
        """
## 
""",
        elem_classes=["md-custom"],
        header_links=True,
    )

    gr.ParamViewer(value=_docs["WebRTC"]["members"]["__init__"], linkify=[])

    demo.load(
        None,
        js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          WebRTC: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""",
    )

demo.launch()
