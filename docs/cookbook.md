

<style>
.tag-button {
    cursor: pointer;
    opacity: 0.5;
    transition: opacity 0.2s ease;
}

.tag-button > code {
    color: var(--supernova);
}

.tag-button.active {
    opacity: 1;
}
</style>

A collection of applications built with FastRTC. Click on the tags below to find the app you're looking for!


<div class="tag-buttons">
  <button class="tag-button" data-tag="audio"><code>audio</code></button>
  <button class="tag-button" data-tag="video"><code>video</code></button>
  <button class="tag-button" data-tag="llm"><code>llm</code></button>
  <button class="tag-button" data-tag="computer-vision"><code>computer-vision</code></button>
  <button class="tag-button" data-tag="real-time-api"><code>real-time-api</code></button>
  <button class="tag-button" data-tag="voice-chat"><code>voice chat</code></button>
  <button class="tag-button" data-tag="code-generation"><code>code generation</code></button>
  <button class="tag-button" data-tag="stopword"><code>stopword</code></button>
  <button class="tag-button" data-tag="transcription"><code>transcription</code></button>
  <button class="tag-button" data-tag="sambanova"><code>SambaNova</code></button>
  <button class="tag-button" data-tag="groq"><code>Groq</code></button>
  <button class="tag-button" data-tag="elevenlabs"><code>ElevenLabs</code></button>
  <button class="tag-button" data-tag="elevenlabs"><code>Kyutai</code></button>
</div>

<script>
function filterCards() {
    const activeButtons = document.querySelectorAll('.tag-button.active');
    const selectedTags = Array.from(activeButtons).map(button => button.getAttribute('data-tag'));
    const cards = document.querySelectorAll('.grid.cards > ul > li > p[data-tags]');
    
    cards.forEach(card => {
        const cardTags = card.getAttribute('data-tags').split(',');
        const shouldShow = selectedTags.length === 0 || selectedTags.some(tag => cardTags.includes(tag));
        card.parentElement.style.display = shouldShow ? 'block' : 'none';
    });
}
document.querySelectorAll('.tag-button').forEach(button => {
    button.addEventListener('click', () => {
        button.classList.toggle('active');
        filterCards();
    });
});
</script>


<div class="grid cards" markdown>

-   :speaking_head:{ .lg .middle }:eyes:{ .lg .middle } __Gemini Audio Video Chat__
{: data-tags="audio,video,real-time-api"}

    ---

    Stream BOTH your webcam video and audio feeds to Google Gemini. You can also upload images to augment your conversation!

    <video width=98% src="https://github.com/user-attachments/assets/9636dc97-4fee-46bb-abb8-b92e69c08c71" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/gemini-audio-video)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/gemini-audio-video)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/gemini-audio-video/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __Google Gemini Real Time Voice API__
{: data-tags="audio,real-time-api,voice-chat"}

    ---

    Talk to Gemini in real time using Google's voice API.

    <video width=98% src="https://github.com/user-attachments/assets/ea6d18cb-8589-422b-9bba-56332d9f61de" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/talk-to-gemini)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/talk-to-gemini-gradio)

    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/talk-to-gemini/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __OpenAI Real Time Voice API__
{: data-tags="audio,real-time-api,voice-chat"}

    ---

    Talk to ChatGPT in real time using OpenAI's voice API.

    <video width=98% src="https://github.com/user-attachments/assets/178bdadc-f17b-461a-8d26-e915c632ff80" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/talk-to-openai)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/talk-to-openai-gradio)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/talk-to-openai/blob/main/app.py)

-   :robot:{ .lg .middle } __Hello Computer__
{: data-tags="llm,stopword,sambanova"}

    ---

    Say computer before asking your question!
    <video width=98% src="https://github.com/user-attachments/assets/afb2a3ef-c1ab-4cfb-872d-578f895a10d5" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/hello-computer)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/hello-computer-gradio)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/hello-computer/blob/main/app.py)

-   :robot:{ .lg .middle } __Llama Code Editor__
{: data-tags="audio,llm,code-generation,groq,stopword"}

    ---

    Create and edit HTML pages with just your voice! Powered by Groq!

    <video width=98% src="https://github.com/user-attachments/assets/98523cf3-dac8-4127-9649-d91a997e3ef5" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/llama-code-editor)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/llama-code-editor/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __Talk to Claude__
{: data-tags="audio,llm,voice-chat"}

    ---

    Use the Anthropic and Play.Ht APIs to have an audio conversation with Claude.

    <video width=98% src="https://github.com/user-attachments/assets/fb6ef07f-3ccd-444a-997b-9bc9bdc035d3" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/talk-to-claude)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/talk-to-claude-gradio)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/talk-to-claude/blob/main/app.py)

-   :musical_note:{ .lg .middle } __LLM Voice Chat__
{: data-tags="audio,llm,voice-chat,groq,elevenlabs"}

    ---

    Talk to an LLM with ElevenLabs!

    <video width=98% src="https://github.com/user-attachments/assets/584e898b-91af-4816-bbb0-dd3216eb80b0" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/llm-voice-chat)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/llm-voice-chat-gradio)

    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/llm-voice-chat/blob/main/app.py)

-   :musical_note:{ .lg .middle } __Whisper Transcription__
{: data-tags="audio,transcription,groq"}

    ---

    Have whisper transcribe your speech in real time!

    <video width=98% src="https://github.com/user-attachments/assets/87603053-acdc-4c8a-810f-f618c49caafb" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/whisper-realtime)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/whisper-realtime-gradio)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/whisper-realtime/blob/main/app.py)

-   :robot:{ .lg .middle } __Talk to Sambanova__
{: data-tags="llm,stopword,sambanova"}

    ---

    Talk to Llama 3.2 with the SambaNova API.
    <video width=98% src="https://github.com/user-attachments/assets/92e4a45a-b5e9-45cd-b7f4-9339ceb343e1" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/talk-to-sambanova)

    [:octicons-arrow-right-24: Gradio UI](https://huggingface.co/spaces/fastrtc/talk-to-sambanova-gradio)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/talk-to-sambanova/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __Hello Llama: Stop Word Detection__
{: data-tags="audio,llm,code-generation,stopword,sambanova"}

    ---

    A code editor built with Llama 3.3 70b that is triggered by the phrase "Hello Llama".
    Build a Siri-like coding assistant in 100 lines of code!

    <video width=98% src="https://github.com/user-attachments/assets/3e10cb15-ff1b-4b17-b141-ff0ad852e613" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/hey-llama-code-editor)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/hey-llama-code-editor/blob/main/app.py)


-   :speaking_head:{ .lg .middle } __Audio Input/Output with mini-omni2__
{: data-tags="audio,llm,voice-chat"}

    ---

    Build a GPT-4o like experience with mini-omni2, an audio-native LLM.

    <video width=98% src="https://github.com/user-attachments/assets/58c06523-fc38-4f5f-a4ba-a02a28e7fa9e" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/mini-omni2-webrtc)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/mini-omni2-webrtc/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __Kyutai Moshi__
{: data-tags="audio,llm,voice-chat,kyutai"}

    ---

    Kyutai's moshi is a novel speech-to-speech model for modeling human conversations.

    <video width=98% src="https://github.com/user-attachments/assets/becc7a13-9e89-4a19-9df2-5fb1467a0137" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/talk-to-moshi)
    
    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/talk-to-moshi/blob/main/app.py)

-   :speaking_head:{ .lg .middle } __Talk to Ultravox__
{: data-tags="audio,llm,voice-chat"}

    ---

    Talk to Fixie.AI's audio-native Ultravox LLM with the transformers library.

    <video width=98% src="https://github.com/user-attachments/assets/e6e62482-518c-4021-9047-9da14cd82be1" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/talk-to-ultravox)

    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/talk-to-ultravox/blob/main/app.py)


-   :speaking_head:{ .lg .middle } __Talk to Llama 3.2 3b__
{: data-tags="audio,llm,voice-chat"}

    ---

    Use the Lepton API to make Llama 3.2 talk back to you!

    <video width=98% src="https://github.com/user-attachments/assets/3ee37a6b-0892-45f5-b801-73188fdfad9a" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/llama-3.2-3b-voice-webrtc)

    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/llama-3.2-3b-voice-webrtc/blob/main/app.py)


-   :robot:{ .lg .middle } __Talk to Qwen2-Audio__
{: data-tags="audio,llm,voice-chat"}

    ---

    Qwen2-Audio is a SOTA audio-to-text LLM developed by Alibaba.

    <video width=98% src="https://github.com/user-attachments/assets/c821ad86-44cc-4d0c-8dc4-8c02ad1e5dc8" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/talk-to-qwen-webrtc)

    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/talk-to-qwen-webrtc/blob/main/app.py)


-   :camera:{ .lg .middle } __Yolov10 Object Detection__
{: data-tags="video,computer-vision"}

    ---

    Run the Yolov10 model on a user webcam stream in real time!

    <video width=98% src="https://github.com/user-attachments/assets/f82feb74-a071-4e81-9110-a01989447ceb" controls style="text-align: center"></video>

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/fastrtc/object-detection)

    [:octicons-code-16: Code](https://huggingface.co/spaces/fastrtc/object-detection/blob/main/app.py)

-   :camera:{ .lg .middle } __Video Object Detection with RT-DETR__
{: data-tags="video,computer-vision"}

    ---

    Upload a video and stream out frames with detected objects (powered by RT-DETR) model.

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/rt-detr-object-detection-webrtc)

    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/rt-detr-object-detection-webrtc/blob/main/app.py)

-   :speaker:{ .lg .middle } __Text-to-Speech with Parler__
{: data-tags="audio"}

    ---

    Stream out audio generated by Parler TTS!

    [:octicons-arrow-right-24: Demo](https://huggingface.co/spaces/freddyaboulton/parler-tts-streaming-webrtc)

    [:octicons-code-16: Code](https://huggingface.co/spaces/freddyaboulton/parler-tts-streaming-webrtc/blob/main/app.py)


</div>
