# Connecting via API

Before continuing, select the `modality`, `mode` of your `Stream` and whether you're using `WebRTC` or `WebSocket`s.

<div class="config-selector">
    <div class="select-group">
        <label for="connection">Connection</label>
        <select id="connection" onchange="updateDocs()">
            <option value="webrtc">WebRTC</option>
            <option value="websocket">WebSocket</option>
        </select>
    </div>
    <div class="select-group">
        <label for="modality">Modality</label>
        <select id="modality" onchange="updateDocs()">
            <option value="audio">Audio</option>
            <option value="video">Video</option>
            <option value="audio-video">Audio-Video</option>
        </select>
    </div>
    <div class="select-group">
        <label for="mode">Mode</label>
        <select id="mode" onchange="updateDocs()">
            <option value="send-receive">Send-Receive</option>
            <option value="receive">Receive</option>
            <option value="send">Send</option>
        </select>
    </div>

</div>

### Sample Code
<div id="docs"></div>

### Message Format

Over both WebRTC and WebSocket, the server can send messages of the following format:

```json
{
    "type": `send_input` | `fetch_output` | `stopword` | `error` | `warning` | `log`,
    "data": string | object
}
```

- `send_input`: Send any input data for the handler to the server. See [`Additional Inputs`](#additional-inputs) for more details.
- `fetch_output`: An instance of [`AdditionalOutputs`](#additional-outputs) is sent to the server.
- `stopword`: The stopword has been detected. See [`ReplyOnStopWords`](../audio/#reply-on-stopwords) for more details.
- `error`: An error occurred. The `data` will be a string containing the error message.
- `warning`: A warning occurred. The `data` will be a string containing the warning message.
- `log`: A log message. The `data` will be a string containing the log message.

The `ReplyOnPause` handler can also send the following `log` messages.

```json
{
    "type": "log",
    "data": "pause_detected" | "response_starting"
}
```

!!! tip
    When using WebRTC, the messages will be encoded as strings, so parse as JSON before using.

### Additional Inputs

When the `send_input` message is received, update the inputs of your handler however you like by using the `set_input` method of the `Stream` object.

A common pattern is to use a `POST` request to send the updated data. The first argument to the `set_input` method is the `webrtc_id` of the handler.

```python
from pydantic import BaseModel, Field

class InputData(BaseModel):
    webrtc_id: str
    conf_threshold: float = Field(ge=0, le=1)


@app.post("/input_hook")
async def _(data: InputData):
    stream.set_input(data.webrtc_id, data.conf_threshold)
```

The updated data will be passed to the handler on the **next** call.

### Additional Outputs

The `fetch_output` message is sent to the client whenever an instance of [`AdditionalOutputs`](../streams/#additional-outputs) is available. You can access the latest output data by calling the `fetch_latest_output` method of the `Stream` object. 

However, rather than fetching each output manually, a common pattern is to fetch the entire stream of output data by calling the `output_stream` method.

Here is an example:
```python
from fastapi.responses import StreamingResponse

@app.get("/updates")
async def stream_updates(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            # Output is the AdditionalOutputs instance
            # Be sure to serialize it however you would like
            yield f"data: {output.args[0]}\n\n"

    return StreamingResponse(
        output_stream(), 
        media_type="text/event-stream"
    )
```

### Handling Errors

When connecting via `WebRTC`, the server will respond to the `/webrtc/offer` route with a JSON response. If there are too many connections, the server will respond with a 429 error.

```json
{
    "status": "failed",
    "meta": {
        "error": "concurrency_limit_reached",
        "limit": 10
    }
```

Over `WebSocket`, the server will send the same message before closing the connection.


<style>
.config-selector {
    margin: 1em 0;
    display: flex;
    gap: 2em;
}

.select-group {
    display: flex;
    flex-direction: column;
    gap: 0.5em;
}

.select-group label {
    font-size: 0.8em;
    font-weight: 600;
    color: var(--md-default-fg-color--light);
}

.select-group select {
    padding: 0.5em;
    border: 1px solid var(--md-default-fg-color--lighter);
    border-radius: 4px;
    background-color: var(--md-code-bg-color);
    color: var(--md-code-fg-color);
    width: 150px;
    font-size: 0.9em;
}

/* Style code blocks to match site theme */
.rendered-content pre {
    background-color: var(--md-code-bg-color) !important;
    color: var(--md-code-fg-color) !important;
    padding: 1em;
    border-radius: 4px;
}

.rendered-content code {
    font-family: var(--md-code-font-family);
    background-color: var(--md-code-bg-color) !important;
    color: var(--md-code-fg-color) !important;
}
</style>

<script>

// doT.js
// 2011-2014, Laura Doktorova, https://github.com/olado/doT
// Licensed under the MIT license.


    var doT = {
        name: "doT",
        version: "1.1.1",
        templateSettings: {
            evaluate: /\{\{([\s\S]+?(\}?)+)\}\}/g,
            interpolate: /\{\{=([\s\S]+?)\}\}/g,
            encode: /\{\{!([\s\S]+?)\}\}/g,
            use: /\{\{#([\s\S]+?)\}\}/g,
            useParams: /(^|[^\w$])def(?:\.|\[[\'\"])([\w$\.]+)(?:[\'\"]\])?\s*\:\s*([\w$\.]+|\"[^\"]+\"|\'[^\']+\'|\{[^\}]+\})/g,
            define: /\{\{##\s*([\w\.$]+)\s*(\:|=)([\s\S]+?)#\}\}/g,
            defineParams: /^\s*([\w$]+):([\s\S]+)/,
            conditional: /\{\{\?(\?)?\s*([\s\S]*?)\s*\}\}/g,
            iterate: /\{\{~\s*(?:\}\}|([\s\S]+?)\s*\:\s*([\w$]+)\s*(?:\:\s*([\w$]+))?\s*\}\})/g,
            varname: "it",
            strip: false,
            append: true,
            selfcontained: false,
            doNotSkipEncoded: false
        },
        template: undefined, //fn, compile template
        compile: undefined, //fn, for express
        log: true
    }, _globals;

    doT.encodeHTMLSource = function (doNotSkipEncoded) {
        var encodeHTMLRules = { "&": "&#38;", "<": "&#60;", ">": "&#62;", '"': "&#34;", "'": "&#39;", "/": "&#47;" },
            matchHTML = doNotSkipEncoded ? /[&<>"'\/]/g : /&(?!#?\w+;)|<|>|"|'|\//g;
        return function (code) {
            return code ? code.toString().replace(matchHTML, function (m) { return encodeHTMLRules[m] || m; }) : "";
        };
    };

    _globals = (function () { return this || (0, eval)("this"); }());

    /* istanbul ignore else */
    if (typeof module !== "undefined" && module.exports) {
        module.exports = doT;
    } else if (typeof define === "function" && define.amd) {
        define(function () { return doT; });
    } else {
        _globals.doT = doT;
    }

    var startend = {
        append: { start: "'+(", end: ")+'", startencode: "'+encodeHTML(" },
        split: { start: "';out+=(", end: ");out+='", startencode: "';out+=encodeHTML(" }
    }, skip = /$^/;

    function resolveDefs(c, block, def) {
        return ((typeof block === "string") ? block : block.toString())
            .replace(c.define || skip, function (m, code, assign, value) {
                if (code.indexOf("def.") === 0) {
                    code = code.substring(4);
                }
                if (!(code in def)) {
                    if (assign === ":") {
                        if (c.defineParams) value.replace(c.defineParams, function (m, param, v) {
                            def[code] = { arg: param, text: v };
                        });
                        if (!(code in def)) def[code] = value;
                    } else {
                        new Function("def", "def['" + code + "']=" + value)(def);
                    }
                }
                return "";
            })
            .replace(c.use || skip, function (m, code) {
                if (c.useParams) code = code.replace(c.useParams, function (m, s, d, param) {
                    if (def[d] && def[d].arg && param) {
                        var rw = (d + ":" + param).replace(/'|\\/g, "_");
                        def.__exp = def.__exp || {};
                        def.__exp[rw] = def[d].text.replace(new RegExp("(^|[^\\w$])" + def[d].arg + "([^\\w$])", "g"), "$1" + param + "$2");
                        return s + "def.__exp['" + rw + "']";
                    }
                });
                var v = new Function("def", "return " + code)(def);
                return v ? resolveDefs(c, v, def) : v;
            });
    }

    function unescape(code) {
        return code.replace(/\\('|\\)/g, "$1").replace(/[\r\t\n]/g, " ");
    }

    doT.template = function (tmpl, c, def) {
        c = c || doT.templateSettings;
        var cse = c.append ? startend.append : startend.split, needhtmlencode, sid = 0, indv,
            str = (c.use || c.define) ? resolveDefs(c, tmpl, def || {}) : tmpl;

        str = ("var out='" + (c.strip ? str.replace(/(^|\r|\n)\t* +| +\t*(\r|\n|$)/g, " ")
            .replace(/\r|\n|\t|\/\*[\s\S]*?\*\//g, "") : str)
            .replace(/'|\\/g, "\\$&")
            .replace(c.interpolate || skip, function (m, code) {
                return cse.start + unescape(code) + cse.end;
            })
            .replace(c.encode || skip, function (m, code) {
                needhtmlencode = true;
                return cse.startencode + unescape(code) + cse.end;
            })
            .replace(c.conditional || skip, function (m, elsecase, code) {
                return elsecase ?
                    (code ? "';}else if(" + unescape(code) + "){out+='" : "';}else{out+='") :
                    (code ? "';if(" + unescape(code) + "){out+='" : "';}out+='");
            })
            .replace(c.iterate || skip, function (m, iterate, vname, iname) {
                if (!iterate) return "';} } out+='";
                sid += 1; indv = iname || "i" + sid; iterate = unescape(iterate);
                return "';var arr" + sid + "=" + iterate + ";if(arr" + sid + "){var " + vname + "," + indv + "=-1,l" + sid + "=arr" + sid + ".length-1;while(" + indv + "<l" + sid + "){"
                    + vname + "=arr" + sid + "[" + indv + "+=1];out+='";
            })
            .replace(c.evaluate || skip, function (m, code) {
                return "';" + unescape(code) + "out+='";
            })
            + "';return out;")
            .replace(/\n/g, "\\n").replace(/\t/g, '\\t').replace(/\r/g, "\\r")
            .replace(/(\s|;|\}|^|\{)out\+='';/g, '$1').replace(/\+''/g, "");
        //.replace(/(\s|;|\}|^|\{)out\+=''\+/g,'$1out+=');

        if (needhtmlencode) {
            if (!c.selfcontained && _globals && !_globals._encodeHTML) _globals._encodeHTML = doT.encodeHTMLSource(c.doNotSkipEncoded);
            str = "var encodeHTML = typeof _encodeHTML !== 'undefined' ? _encodeHTML : ("
                + doT.encodeHTMLSource.toString() + "(" + (c.doNotSkipEncoded || '') + "));"
                + str;
        }
        try {
            return new Function(c.varname, str);
        } catch (e) {
            /* istanbul ignore else */
            if (typeof console !== "undefined") console.log("Could not create a template function: " + str);
            throw e;
        }
    };

    doT.compile = function (tmpl, def) {
        return doT.template(tmpl, null, def);
    };

// WebRTC template

const webrtcTemplate = doT.template(`
To connect to the server, you need to create a new RTCPeerConnection object and call the \`setupWebRTC\` function below.
{{? it.mode === "send-receive" || it.mode === "receive" }}
This code snippet assumes there is an html element with an id of \`{{=it.modality}}_output_component_id\` where the output will be displayed. It should be {{? it.modality === "audio"}}a \`<audio>\`{{??}}an \`<video>\`{{?}} element.
{{?}}

\`\`\`javascript
// pass any rtc_configuration params here
const pc = new RTCPeerConnection();
{{? it.mode === "send-receive" || it.mode === "receive" }}
const {{=it.modality}}_output_component = document.getElementById("{{=it.modality}}_output_component_id");
{{?}}                     
async function setupWebRTC(peerConnection) {
    {{? it.mode === "send-receive" || it.mode === "send" }}      
    // Get {{=it.modality}} stream from webcam
    const stream = await navigator.mediaDevices.getUserMedia({
        {{=it.modality}}: true,
    })
    {{?}}
    {{? it.mode === "send-receive" }}
    //  Send {{=it.modality}} stream to server
    stream.getTracks().forEach(async (track) => {
        const sender = pc.addTrack(track, stream);
    })
    {{?? it.mode === "send" }}
    // Receive {{=it.modality}} stream from server
    pc.addTransceiver({{=it.modality}}, { direction: "recvonly" })
    {{?}}
    {{? it.mode === "send-receive" || it.mode === "receive" }}
    peerConnection.addEventListener("track", (evt) => {
        if ({{=it.modality}}_output_component && 
            {{=it.modality}}_output_component.srcObject !== evt.streams[0]) {
            {{=it.modality}}_output_component.srcObject = evt.streams[0];
        }
    });
    {{?}}
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
\`\`\`
`);

// WebSocket template
const wsTemplate = doT.template(`
{{? it.modality !== "audio" || it.mode !== "send-receive" }}
WebSocket connections are currently only supported for audio in send-receive mode.
{{??}}

To connect to the server via WebSocket, you'll need to establish a WebSocket connection and handle audio processing. The code below assumes there is an HTML audio element for output playback.

\`\`\`javascript
// Setup audio context and stream
const audioContext = new AudioContext();
const stream = await navigator.mediaDevices.getUserMedia({
    audio: true
});

// Create WebSocket connection
const ws = new WebSocket(\`\${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//$\{window.location.host}/websocket/offer\`);

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
\`\`\`
{{?}}
`);

function updateDocs() {
    // Get selected values
    const modality = document.getElementById('modality').value;
    const mode = document.getElementById('mode').value;
    const connection = document.getElementById('connection').value;

    // Context for templates
    const context = {
        modality: modality,
        mode: mode,
        additional_inputs: true,
        additional_outputs: true
    };

    // Choose template based on connection type
    const template = connection === 'webrtc' ? webrtcTemplate : wsTemplate;
    
    // Render docs with syntax highlighting
    const html = template(context);
    const docsDiv = document.getElementById('docs');
    docsDiv.innerHTML = marked.parse(html);
    docsDiv.className = 'rendered-content';

    // Initialize any code blocks that were just added
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Initial render
document.addEventListener('DOMContentLoaded', updateDocs);
</script>

