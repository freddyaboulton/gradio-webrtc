---
tags: [gradio-custom-component, Video, streaming, webrtc, realtime]
title: gradio_webrtc
short_description: Stream images in realtime with webrtc
colorFrom: blue
colorTo: yellow
sdk: gradio
pinned: false
app_file: space.py
---

# `gradio_webrtc`
<a href="https://pypi.org/project/gradio_webrtc/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_webrtc"></a>  

Stream images in realtime with webrtc

## Installation

```bash
pip install gradio_webrtc
```

## Usage

```python
import gradio as gr
import cv2
from huggingface_hub import hf_hub_download
from gradio_webrtc import WebRTC
from twilio.rest import Client
import os
from inference import YOLOv10

model_file = hf_hub_download(
    repo_id="onnx-community/yolov10n", filename="onnx/model.onnx"
)

model = YOLOv10(model_file)

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if account_sid and auth_token:
    client = Client(account_sid, auth_token)

    token = client.tokens.create()

    rtc_configuration = {
        "iceServers": token.ice_servers,
        "iceTransportPolicy": "relay",
    }
else:
    rtc_configuration = None


def detection(image, conf_threshold=0.3):
    image = cv2.resize(image, (model.input_width, model.input_height))
    new_image = model.detect_objects(image, conf_threshold)
    return cv2.resize(new_image, (500, 500))


css = """.my-group {max-width: 600px !important; max-height: 600 !important;}
                      .my-column {display: flex !important; justify-content: center !important; align-items: center !important};"""


with gr.Blocks(css=css) as demo:
    gr.HTML(
        """
    <h1 style='text-align: center'>
    YOLOv10 Webcam Stream (Powered by WebRTC ⚡️)
    </h1>
    """
    )
    gr.HTML(
        """
        <h3 style='text-align: center'>
        <a href='https://arxiv.org/abs/2405.14458' target='_blank'>arXiv</a> | <a href='https://github.com/THU-MIG/yolov10' target='_blank'>github</a>
        </h3>
        """
    )
    with gr.Column(elem_classes=["my-column"]):
        with gr.Group(elem_classes=["my-group"]):
            image = WebRTC(label="Stream", rtc_configuration=rtc_configuration)
            conf_threshold = gr.Slider(
                label="Confidence Threshold",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                value=0.30,
            )

        image.stream(
            fn=detection, inputs=[image, conf_threshold], outputs=[image], time_limit=10
        )

if __name__ == "__main__":
    demo.launch()

```

## `WebRTC`

### Initialization

<table>
<thead>
<tr>
<th align="left">name</th>
<th align="left" style="width: 25%;">type</th>
<th align="left">default</th>
<th align="left">description</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left"><code>value</code></td>
<td align="left" style="width: 25%;">

```python
None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">path or URL for the default value that WebRTC component is going to take. Can also be a tuple consisting of (video filepath, subtitle filepath). If a subtitle file is provided, it should be of type .srt or .vtt. Or can be callable, in which case the function will be called whenever the app loads to set the initial value of the component.</td>
</tr>

<tr>
<td align="left"><code>height</code></td>
<td align="left" style="width: 25%;">

```python
int | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">The height of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.</td>
</tr>

<tr>
<td align="left"><code>width</code></td>
<td align="left" style="width: 25%;">

```python
int | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">The width of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.</td>
</tr>

<tr>
<td align="left"><code>label</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">the label for this component. Appears above the component and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component is assigned to.</td>
</tr>

<tr>
<td align="left"><code>every</code></td>
<td align="left" style="width: 25%;">

```python
Timer | float | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.</td>
</tr>

<tr>
<td align="left"><code>inputs</code></td>
<td align="left" style="width: 25%;">

```python
Component | Sequence[Component] | set[Component] | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise). `value` is recalculated any time the inputs change.</td>
</tr>

<tr>
<td align="left"><code>show_label</code></td>
<td align="left" style="width: 25%;">

```python
bool | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">if True, will display label.</td>
</tr>

<tr>
<td align="left"><code>container</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">if True, will place the component in a container - providing some extra padding around the border.</td>
</tr>

<tr>
<td align="left"><code>scale</code></td>
<td align="left" style="width: 25%;">

```python
int | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.</td>
</tr>

<tr>
<td align="left"><code>min_width</code></td>
<td align="left" style="width: 25%;">

```python
int
```

</td>
<td align="left"><code>160</code></td>
<td align="left">minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.</td>
</tr>

<tr>
<td align="left"><code>interactive</code></td>
<td align="left" style="width: 25%;">

```python
bool | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">if True, will allow users to upload a video; if False, can only be used to display videos. If not provided, this is inferred based on whether the component is used as an input or output.</td>
</tr>

<tr>
<td align="left"><code>visible</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">if False, component will be hidden.</td>
</tr>

<tr>
<td align="left"><code>elem_id</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">an optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.</td>
</tr>

<tr>
<td align="left"><code>elem_classes</code></td>
<td align="left" style="width: 25%;">

```python
list[str] | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">an optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.</td>
</tr>

<tr>
<td align="left"><code>render</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">if False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.</td>
</tr>

<tr>
<td align="left"><code>key</code></td>
<td align="left" style="width: 25%;">

```python
int | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">if assigned, will be used to assume identity across a re-render. Components that have the same key across a re-render will have their value preserved.</td>
</tr>

<tr>
<td align="left"><code>mirror_webcam</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">if True webcam will be mirrored. Default is True.</td>
</tr>

<tr>
<td align="left"><code>rtc_configuration</code></td>
<td align="left" style="width: 25%;">

```python
dict[str, Any] | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>time_limit</code></td>
<td align="left" style="width: 25%;">

```python
float | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>mode</code></td>
<td align="left" style="width: 25%;">

```python
Literal["send-receive", "receive"]
```

</td>
<td align="left"><code>"send-receive"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>modality</code></td>
<td align="left" style="width: 25%;">

```python
Literal["video", "audio"]
```

</td>
<td align="left"><code>"video"</code></td>
<td align="left">None</td>
</tr>
</tbody></table>


### Events

| name | description |
|:-----|:------------|
| `tick` |  |



### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As output:** Is passed, passes the uploaded video as a `str` filepath or URL whose extension can be modified by `format`.
- **As input:** Should return, expects a {str} or {pathlib.Path} filepath to a video which is displayed, or a {Tuple[str | pathlib.Path, str | pathlib.Path | None]} where the first element is a filepath to a video and the second element is an optional filepath to a subtitle file.

 ```python
 def predict(
     value: str
 ) -> typing.Any:
     return value
 ```
 
