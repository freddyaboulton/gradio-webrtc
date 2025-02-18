## Demo does not work when deploying to the cloud

Make sure you are using a TURN server. See [deployment](../deployment).

## Recorded input audio sounds muffled during output audio playback

By default, the microphone is [configured](https://github.com/freddyaboulton/gradio-webrtc/blob/903f1f70bd586f638ad3b5a3940c7a8ec70ad1f5/backend/gradio_webrtc/webrtc.py#L575) to do echo cancellation.
This is what's causing the recorded audio to sound muffled when the streamed audio starts playing.
You can disable this via the `track_constraints` (see [Advanced Configuration](../advanced-configuration)) with the following code:

```python
stream = Stream(
    track_constraints={
            "echoCancellation": False,
            "noiseSuppression": {"exact": True},
            "autoGainControl": {"exact": True},
            "sampleRate": {"ideal": 24000},
            "sampleSize": {"ideal": 16},
            "channelCount": {"exact": 1},
        },
    rtc_configuration=None,
    mode="send-receive",
    modality="audio",
)
```

## How to raise errors in the UI

You can raise `WebRTCError` in order for an error message to show up in the user's screen. This is similar to how `gr.Error` works.

!!! warning

    The `WebRTCError` class is only supported in the `WebRTC` component.

Here is a simple example:

```python
def generation(num_steps):
    for _ in range(num_steps):
        segment = AudioSegment.from_file(
            "/Users/freddy/sources/gradio/demo/audio_debugger/cantina.wav"
        )
        yield (
            segment.frame_rate,
            np.array(segment.get_array_of_samples()).reshape(1, -1),
        )
        time.sleep(3.5)
    raise WebRTCError("This is a test error")

with gr.Blocks() as demo:
    audio = WebRTC(
    label="Stream",
    mode="receive",
    modality="audio",
    )
    num_steps = gr.Slider(
        label="Number of Steps",
        minimum=1,
        maximum=10,
        step=1,
        value=5,
    )
    button = gr.Button("Generate")

    audio.stream(
        fn=generation, inputs=[num_steps], outputs=[audio], trigger=button.click
    )

demo.launch()
```