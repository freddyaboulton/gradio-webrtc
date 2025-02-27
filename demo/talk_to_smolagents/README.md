---
title: Talk to Smolagents
emoji: 💻
colorFrom: purple
colorTo: red
sdk: gradio
sdk_version: 5.16.0
app_file: app.py
pinned: false
license: mit
short_description: FastRTC Voice Agent with smolagents
tags: [webrtc, websocket, gradio, secret|HF_TOKEN]
---

# Voice LLM Agent with Image Generation

A voice-enabled AI assistant powered by FastRTC that can:
1. Stream audio in real-time using WebRTC
2. Listen and respond with natural pauses in conversation
3. Generate images based on your requests
4. Maintain conversation context across exchanges

This app combines the real-time communication capabilities of FastRTC with the powerful agent framework of smolagents.

## Key Features

- **Real-time Streaming**: Uses FastRTC's WebRTC-based audio streaming
- **Voice Activation**: Automatic detection of speech pauses to trigger responses
- **Multi-modal Interaction**: Combines voice and image generation in a single interface

## Setup

1. Install Python 3.9+ and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following:
   ```
   HF_TOKEN=your_huggingface_api_key
   MODE=UI  # Use 'UI' for Gradio interface, leave blank for HTML interface
   ```

## Running the App

### With Gradio UI (Recommended)

```bash
MODE=UI python app.py
```

This launches a Gradio UI at http://localhost:7860 with:
- FastRTC's built-in streaming audio components
- A chat interface showing the conversation
- An image display panel for generated images

## How to Use

1. Click the microphone button to start streaming your voice.
2. Speak naturally - the app will automatically detect when you pause.
3. Ask the agent to generate an image, for example:
   - "Create an image of a magical forest with glowing mushrooms."
   - "Generate a picture of a futuristic city with flying cars."
4. View the generated image and hear the agent's response.

## Technical Architecture

### FastRTC Components

- **Stream**: Core component that handles WebRTC connections and audio streaming
- **ReplyOnPause**: Detects when the user stops speaking to trigger a response
- **get_stt_model/get_tts_model**: Provides optimized speech-to-text and text-to-speech models

### smolagents Components

- **CodeAgent**: Intelligent agent that can use tools based on natural language inputs
- **Tool.from_space**: Integration with Hugging Face Spaces for image generation
- **HfApiModel**: Connection to powerful language models for understanding requests

### Integration Flow

1. FastRTC streams and processes audio input in real-time
2. Speech is converted to text and passed to the smolagents CodeAgent
3. The agent processes the request and calls tools when needed
4. Responses and generated images are streamed back through FastRTC
5. The UI updates to show both text responses and generated images

## Advanced Features

- Conversation history is maintained across exchanges
- Error handling ensures the app continues working even if agent processing fails
- The application leverages FastRTC's streaming capabilities for efficient audio transmission