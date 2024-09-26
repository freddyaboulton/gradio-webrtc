import gradio as gr
from app import demo as app
import os

_docs = {
    "WebRTC": {
        "description": "Creates a video component that can be used to upload/record videos (as an input) or display videos (as an output).\nFor the video to be playable in the browser it must have a compatible container and codec combination. Allowed\ncombinations are .mp4 with h264 codec, .ogg with theora codec, and .webm with vp9 codec. If the component detects\nthat the output video would not be playable in the browser it will attempt to convert it to a playable mp4 video.\nIf the conversion fails, the original video is returned.\n",
        "members": {
            "__init__": {
                "value": {
                    "type": "str\n    | Path\n    | tuple[str | Path, str | Path | None]\n    | Callable\n    | None",
                    "default": "None",
                    "description": "path or URL for the default value that WebRTC component is going to take. Can also be a tuple consisting of (video filepath, subtitle filepath). If a subtitle file is provided, it should be of type .srt or .vtt. Or can be callable, in which case the function will be called whenever the app loads to set the initial value of the component.",
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
                "every": {
                    "type": "Timer | float | None",
                    "default": "None",
                    "description": "continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.",
                },
                "inputs": {
                    "type": "Component | Sequence[Component] | set[Component] | None",
                    "default": "None",
                    "description": "components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise). `value` is recalculated any time the inputs change.",
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
                "show_share_button": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will show a share icon in the corner of the component that allows user to share outputs to Hugging Face Spaces Discussions. If False, icon does not appear. If set to None (default behavior), then the icon appears if this Gradio app is launched on Spaces, but not otherwise.",
                },
                "show_download_button": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will show a download icon in the corner of the component that allows user to download the output. If False, icon does not appear. By default, it will be True for output components and False for input components.",
                },
                "min_length": {
                    "type": "int | None",
                    "default": "None",
                    "description": "the minimum length of video (in seconds) that the user can pass into the prediction function. If None, there is no minimum length.",
                },
                "max_length": {
                    "type": "int | None",
                    "default": "None",
                    "description": "the maximum length of video (in seconds) that the user can pass into the prediction function. If None, there is no maximum length.",
                },
                "rtc_configuration": {
                    "type": "dict[str, Any] | None",
                    "default": "None",
                    "description": None,
                },
            },
            "postprocess": {
                "value": {
                    "type": "typing.Any",
                    "description": "Expects a {str} or {pathlib.Path} filepath to a video which is displayed, or a {Tuple[str | pathlib.Path, str | pathlib.Path | None]} where the first element is a filepath to a video and the second element is an optional filepath to a subtitle file.",
                }
            },
            "preprocess": {
                "return": {
                    "type": "str",
                    "description": "Passes the uploaded video as a `str` filepath or URL whose extension can be modified by `format`.",
                },
                "value": None,
            },
        },
        "events": {"tick": {"type": None, "default": None, "description": ""}},
    },
    "__meta__": {"additional_interfaces": {}, "user_fn_refs": {"WebRTC": []}},
}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
        """
# `gradio_webrtc`

<div style="display: flex; gap: 7px;">
<img alt="Static Badge" src="https://img.shields.io/badge/version%20-%200.0.1%20-%20orange">  
</div>

Stream images in realtime with webrtc
""",
        elem_classes=["md-custom"],
        header_links=True,
    )
    app.render()
    gr.Markdown(
        """
## Installation

```bash
pip install gradio_webrtc
```

## Usage

```python
import gradio as gr
import cv2
import numpy as np
from gradio_webrtc import WebRTC
from pathlib import Path
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

CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

directory = Path(__file__).parent

MODEL = str((directory / "MobileNetSSD_deploy.caffemodel").resolve())
PROTOTXT = str((directory / "MobileNetSSD_deploy.prototxt.txt").resolve())
net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)


def detection(image, conf_threshold=0.3):

    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5
    )
    net.setInput(blob)

    detections = net.forward()
    image = cv2.resize(image, (500, 500))
    (h, w) = image.shape[:2]
    labels = []
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > conf_threshold:
            # extract the index of the class label from the `detections`,
            # then compute the (x, y)-coordinates of the bounding box for
            # the object
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # display the prediction
            label = f"{CLASSES[idx]}: {round(confidence * 100, 2)}%"
            labels.append(label)
            cv2.rectangle(image, (startX, startY), (endX, endY), COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(
                image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2
            )
    return image


css=\"\"\".my-group {max-width: 600px !important; max-height: 600 !important;}
                      .my-column {display: flex !important; justify-content: center !important; align-items: center !important};\"\"\"


with gr.Blocks(css=css) as demo:
    gr.HTML(
        \"\"\"
    <h1 style='text-align: center'>
    YOLOv10 Webcam Stream
    </h1>
    \"\"\")
    gr.HTML(
        \"\"\"
        <h3 style='text-align: center'>
        <a href='https://arxiv.org/abs/2405.14458' target='_blank'>arXiv</a> | <a href='https://github.com/THU-MIG/yolov10' target='_blank'>github</a>
        </h3>
        \"\"\")
    with gr.Column(elem_classes=["my-column"]):
        with gr.Group(elem_classes=["my-group"]):
            image = WebRTC(label="Strean", rtc_configuration=rtc_configuration)
            conf_threshold = gr.Slider(
                label="Confidence Threshold",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                value=0.30,
            )
        
        image.webrtc_stream(
            fn=detection,
            inputs=[image],
            stream_every=0.05,
            time_limit=30
        )

if __name__ == '__main__':
    demo.launch()

```
""",
        elem_classes=["md-custom"],
        header_links=True,
    )

    gr.Markdown(
        """
## `WebRTC`

### Initialization
""",
        elem_classes=["md-custom"],
        header_links=True,
    )

    gr.ParamViewer(value=_docs["WebRTC"]["members"]["__init__"], linkify=[])

    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["WebRTC"]["events"], linkify=["Event"])

    gr.Markdown(
        """

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, passes the uploaded video as a `str` filepath or URL whose extension can be modified by `format`.
- **As output:** Should return, expects a {str} or {pathlib.Path} filepath to a video which is displayed, or a {Tuple[str | pathlib.Path, str | pathlib.Path | None]} where the first element is a filepath to a video and the second element is an optional filepath to a subtitle file.

 ```python
def predict(
    value: str
) -> typing.Any:
    return value
```
""",
        elem_classes=["md-custom", "WebRTC-user-fn"],
        header_links=True,
    )

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
