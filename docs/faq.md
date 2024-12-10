## Demo does not work when deploying to the cloud

Make sure you are using a TURN server. See [deployment](/deployment).

## Recorded input audio sounds muffled during output audio playback

By default, the microphone is [configured](https://github.com/freddyaboulton/gradio-webrtc/blob/903f1f70bd586f638ad3b5a3940c7a8ec70ad1f5/backend/gradio_webrtc/webrtc.py#L575) to do echoCancellation.
This is what's causing the recorded audio to sound muffled when the streamed audio starts playing.
You can disable this via the `track_constraints` (see [advanced configuration](./advanced-configuration])) with the following code:

```python
	audio = WebRTC(
		label="Stream",
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