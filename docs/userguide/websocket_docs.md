# FastRTC WebSocket Docs

{% if modality != "audio" or mode != "send-receive" %}
WebSocket connections are currently only supported for audio in send-receive mode.
{% else %}

## Connecting

To connect to the server via WebSocket, you'll need to establish a WebSocket connection and handle audio processing. The code below assumes there is an HTML audio element for output playback.

```js
// Setup audio context and stream
const audioContext = new AudioContext();
const stream = await navigator.mediaDevices.getUserMedia({
    audio: true
});

// Create WebSocket connection
const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/websocket/offer`);

ws.onopen = () => {
    // Send initial start message with unique ID
    ws.send(JSON.stringify({
        event: "start",
        websocket_id: generateId()  // Implement your own ID generator
    }));

    // Setup audio processing
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(2048, 1, 1);
    source.connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const mulawData = convertToMulaw(inputData, audioContext.sampleRate);
        const base64Audio = btoa(String.fromCharCode.apply(null, mulawData));
        
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                event: "media",
                media: {
                    payload: base64Audio
                }
            }));
        }
    };
};

// Handle incoming audio
const outputContext = new AudioContext({ sampleRate: 24000 });
let audioQueue = [];
let isPlaying = false;

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === "media") {
        // Process received audio
        const audioData = atob(data.media.payload);
        const mulawData = new Uint8Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            mulawData[i] = audioData.charCodeAt(i);
        }

        // Convert mu-law to linear PCM
        const linearData = alawmulaw.mulaw.decode(mulawData);
        const audioBuffer = outputContext.createBuffer(1, linearData.length, 24000);
        const channelData = audioBuffer.getChannelData(0);
        
        for (let i = 0; i < linearData.length; i++) {
            channelData[i] = linearData[i] / 32768.0;
        }

        audioQueue.push(audioBuffer);
        if (!isPlaying) {
            playNextBuffer();
        }
    }
};

function playNextBuffer() {
    if (audioQueue.length === 0) {
        isPlaying = false;
        return;
    }

    isPlaying = true;
    const bufferSource = outputContext.createBufferSource();
    bufferSource.buffer = audioQueue.shift();
    bufferSource.connect(outputContext.destination);
    bufferSource.onended = playNextBuffer;
    bufferSource.start();
}
```

Note: This implementation requires the `alawmulaw` library for audio encoding/decoding:
```html
<script src="https://cdn.jsdelivr.net/npm/alawmulaw"></script>
```

## Handling Input Requests

When the server requests additional input data, it will send a `send_input` message over the WebSocket. You should handle this by sending the data to your input hook:

```js
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle send_input messages
    if (data?.type === "send_input") {
        fetch('/input_hook', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                webrtc_id: websocket_id,  // Use the same ID from connection
                inputs: your_input_data 
            })
        });
    }
    // ... existing audio handling code ...
};
```

## Receiving Additional Outputs

To receive additional outputs from the server, you can use Server-Sent Events (SSE):

```js
const eventSource = new EventSource('/outputs?webrtc_id=' + websocket_id);
eventSource.addEventListener("output", (event) => {
    const eventJson = JSON.parse(event.data);
    // Handle the output data here
    console.log("Received output:", eventJson);
});
```

## Stopping

To stop the WebSocket connection:

```js
function stop(ws) {
    if (ws) {
        ws.send(JSON.stringify({
            event: "stop"
        }));
        ws.close();
    }
}
```

{% endif %}
