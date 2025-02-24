# Audio-Video Streaming

You can simultaneously stream audio and video using `AudioVideoStreamHandler` or `AsyncAudioVideoStreamHandler`.
They are identical to the audio `StreamHandlers` with the addition of `video_receive` and `video_emit` methods which take and return a `numpy` array, respectively.

Here is an example of the video handling functions for connecting with the Gemini multimodal API. In this case, we simply reflect the webcam feed back to the user but every second we'll send the latest webcam frame (and an additional image component) to the Gemini server.

Please see the "Gemini Audio Video Chat" example in the [cookbook](../../cookbook) for the complete code.

``` python title="Async Gemini Video Handling"

async def video_receive(self, frame: np.ndarray):
    """Send video frames to the server"""
    if self.session:
        # send image every 1 second
        # otherwise we flood the API
        if time.time() - self.last_frame_time > 1:
            self.last_frame_time = time.time()
            await self.session.send(encode_image(frame))
            if self.latest_args[2] is not None:
                await self.session.send(encode_image(self.latest_args[2]))
    self.video_queue.put_nowait(frame)

async def video_emit(self) -> VideoEmitType:
    """Return video frames to the client"""
    return await self.video_queue.get()
```