# FastRTC Docs

## Connecting

To connect to the server, you need to create a new RTCPeerConnection object and call the `setupWebRTC` function below.
{% if mode in ["send-receive", "receive"] %}
This code snippet assumes there is an html element with an id of `{{ modality }}_output_component_id` where the output will be displayed. It should be {{ "a `<audio>`" if modality == "audio" else "an `<video>`"}} element.
{% endif %}

```js
// pass any rtc_configuration params here
const pc = new RTCPeerConnection();
{% if mode in ["send-receive", "receive"] %}
const {{modality}}_output_component = document.getElementById("{{modality}}_output_component_id");
{% endif %}                     
async function setupWebRTC(peerConnection) {
    {%- if mode in ["send-receive", "send"] -%}      
    // Get {{modality}} stream from webcam
    const stream = await navigator.mediaDevices.getUserMedia({
        {{modality}}: true,
    })
    {%- endif -%}
    {% if mode == "send-receive" %}

    //  Send {{ self.modality }} stream to server
    stream.getTracks().forEach(async (track) => {
        const sender = pc.addTrack(track, stream);
    })
    {% elif mode == "send" %}
    // Receive {self.modality} stream from server
    pc.addTransceiver({{modality}}, { direction: "recvonly" })
    {%- endif -%}
    {% if mode in ["send-receive", "receive"] %}
    peerConnection.addEventListener("track", (evt) => {
        if ({{modality}}_output_component && 
            {{modality}}_output_component.srcObject !== evt.streams[0]) {
            {{modality}}_output_component.srcObject = evt.streams[0];
        }
    });
    {% endif %}
    // Create data channel (needed!)
    const dataChannel = peerConnection.createDataChannel("text");

    // Create and send offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    // Send offer to server
    const response = await fetch('/webrtc/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sdp: offer.sdp,
            type: offer.type,
            webrtc_id: Math.random().toString(36).substring(7)
        })
    });

    // Handle server response
    const serverResponse = await response.json();
    await peerConnection.setRemoteDescription(serverResponse);
}
```

{%if additional_inputs %}
## Sending Input Data

Your python handler can request additional data from the frontend by calling the `fetch_args()` method (see [here](#add docs)).

This will send a `send_input` message over the WebRTC data channel.
Upon receiving this message, you should trigger the `set_input` hook of your stream.
A simple way to do this is with a `POST` request.

```python
@stream.post("/input_hook")
def _(data: PydanticBody):
    stream.set_inputs(data.webrtc_id, data.inputs)
```

And then in your client code:

```js
const data_channel = peerConnection.createDataChannel("text");

data_channel.onmessage = (event) => {
    event_json = JSON.parse(event.data);
    if (event_json.type === "send_input") {
        fetch('/input_hook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: inputs
        }
            )
        };
    };
```


The `set_inputs` hook will set the `latest_args` property of your stream to whatever the second argument is.

NOTE: It is completely up to you how you want to call the `set_inputs` hook.
Here we use a `POST` request but you can use a websocket or any other protocol.

{% endif %}

{% if additional_outputs %}
## Fetching Output Data
Your python handler can send additional data to the front end by returning or yielding `AdditionalOutputs(...)`. See the [docs](https://freddyaboulton.github.io/gradio-webrtc/user-guide/#additional-outputs).

Your front end can fetch these outputs by calling the `get_outputs` hook of the `Stream`.
Here is an example using `server-sent-events`:

```python
@stream.get("/outputs")
def _(webrtc_id: str)
    async def get_outputs():
        while True:
            for output in stream.get_output(webrtc_id):
                # Serialize to a string prior to this step
                yield f"data: {output}\n\n"
            await
    return StreamingResponse(get_outputs(),  media_type="text/event-stream")
```

NOTE: It is completely up to you how you want to call the `get_output` hook.
Here we use a `server-sent-events` but you can use whatever protocol you want!

{% endif %}


## Stopping

You can stop the stream by calling the following function:

```js
function stop(pc) {
  // close transceivers
  if (pc.getTransceivers) {
    pc.getTransceivers().forEach((transceiver) => {
      if (transceiver.stop) {
        transceiver.stop();
      }
    });
  }

  // close local audio / video
  if (pc.getSenders()) {
    pc.getSenders().forEach((sender) => {
      if (sender.track && sender.track.stop) sender.track.stop();
    });
  }

  // close peer connection
  setTimeout(() => {
    pc.close();
  }, 500);
}
```