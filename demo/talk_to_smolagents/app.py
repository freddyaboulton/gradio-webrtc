from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from fastrtc import (
    get_stt_model,
    get_tts_model,
    Stream,
    ReplyOnPause,
    get_twilio_turn_credentials,
)
from smolagents import CodeAgent, HfApiModel, DuckDuckGoSearchTool

# Load environment variables
load_dotenv()

# Initialize file paths
curr_dir = Path(__file__).parent

# Initialize models
stt_model = get_stt_model()
tts_model = get_tts_model()

# Conversation state to maintain history
conversation_state: List[Dict[str, str]] = []

# System prompt for agent
system_prompt = """You are a helpful assistant that can helps with finding places to 
workremotely from. You should specifically check against reviews and ratings of the 
place. You should use this criteria to find the best place to work from:
- Price
- Reviews
- Ratings
- Location
- WIFI
Only return the name, address of the place, and a short description of the place.
Always search for real places.
Only return real places, not fake ones.
If you receive anything other than a location, you should ask for a location.
<example>
User: I am in Paris, France. Can you find me a place to work from?
Assistant: I found a place called "Le Café de la Paix" at 123 Rue de la Paix, 
Paris, France. It has good reviews and is in a great location.
</example>
<example>
User: I am in London, UK. Can you find me a place to work from?
Assistant: I found a place called "The London Coffee Company".
</example>
<example>
User: How many people are in the room?
Assistant: I only respond to requests about finding places to work from.
</example>

"""

model = HfApiModel(provider="together", model="Qwen/Qwen2.5-Coder-32B-Instruct")

agent = CodeAgent(
    tools=[
        DuckDuckGoSearchTool(),
    ],
    model=model,
    max_steps=10,
    verbosity_level=2,
    description="Search the web for cafes to work from.",
)


def process_response(audio):
    """Process audio input and generate LLM response with TTS"""
    # Convert speech to text using STT model
    text = stt_model.stt(audio)
    if not text.strip():
        return

    input_text = f"{system_prompt}\n\n{text}"
    # Get response from agent
    response_content = agent.run(input_text)

    # Convert response to audio using TTS model
    for audio_chunk in tts_model.stream_tts_sync(response_content or ""):
        # Yield the audio chunk
        yield audio_chunk


stream = Stream(
    handler=ReplyOnPause(process_response, input_sample_rate=16000),
    modality="audio",
    mode="send-receive",
    ui_args={
        "pulse_color": "rgb(255, 255, 255)",
        "icon_button_color": "rgb(255, 255, 255)",
        "title": "🧑‍💻The Coworking Agent",
    },
    rtc_configuration=get_twilio_turn_credentials(),
)

if __name__ == "__main__":
    stream.ui.launch(server_port=7860)
