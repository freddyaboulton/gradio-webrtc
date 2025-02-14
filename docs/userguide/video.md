# Video Streaming

## Input/Output Streaming

We already saw this example in the [Quickstart](../../#quickstart) and the [Core Concepts](../streams) section.

=== "Code"
    
    ``` py title="Input/Output Streaming"
    from fastrtc import Stream
    import gradio as gr

    def detection(image, conf_threshold=0.3): # (1)
        processed_frame = process_frame(image, conf_threshold)
        return processed_frame # (2)

    stream = Stream(
        handler=detection,
        modality="video",
        mode="send-receive", # (3)
        additional_inputs=[
            gr.Slider(minimum=0, maximum=1, step=0.01, value=0.3)
        ],
    )
    ```

    1. The webcam frame will be represented as a numpy array of shape (height, width, RGB).
    2. The function must return a numpy array. It can take arbitrary values from other components.
    3. Set the `modality="video"` and `mode="send-receive"`
=== "Notes"
    1. The webcam frame will be represented as a numpy array of shape (height, width, RGB).
    2. The function must return a numpy array. It can take arbitrary values from other components.
    3. Set the `modality="video"` and `mode="send-receive"`

## Server-to-Client Only

In this case, we stream from the server to the client so we will write a generator function that yields the next frame from the video (as a numpy array)
and set the `mode="receive"` in the `WebRTC` component.

=== "Code"
    ``` py title="Server-To-Client"
    from fastrtc import Stream

    def generation():
        url = "https://download.tsi.telecom-paristech.fr/gpac/dataset/dash/uhd/mux_sources/hevcds_720p30_2M.mp4"
        cap = cv2.VideoCapture(url)
        iterating = True
        while iterating:
            iterating, frame = cap.read()
            yield frame

    stream = Stream(
        handler=generation,
        modality="video",
        mode="receive"
    )
    ```
