<h1 style='text-align: center; margin-bottom: 1rem; color: white;'> Gradio WebRTC ⚡️ </h1>

<div style="display: flex; flex-direction: row; justify-content: center">
<img style="display: block; padding-right: 5px; height: 20px;" alt="Static Badge" src="https://img.shields.io/pypi/v/gradio_webrtc"> 
<a href="https://github.com/freddyaboulton/gradio-webrtc" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/github-white?logo=github&logoColor=black"></a>
</div>

<h3 style='text-align: center'>
Stream video and audio in real time with Gradio using WebRTC. 
</h3>

## Installation

```bash
pip install gradio_webrtc
```

to use built-in pause detection (see [Audio Streaming](https://freddyaboulton.github.io/gradio-webrtc/user-guide/#reply-on-pause)), install the `vad` extra:

```bash
pip install gradio_webrtc[vad]
```

For stop word detection (see [Hello Llama]()), install the `stopword` extra:
```bash
pip install gradio_webrtc[stopword]
```

## Examples
See the [cookbook](/cookbook)