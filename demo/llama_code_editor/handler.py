import base64
import os
import re
from pathlib import Path

import numpy as np
import openai
from dotenv import load_dotenv
from fastrtc import (
    AdditionalOutputs,
    ReplyOnPause,
    audio_to_bytes,
)
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

client = openai.OpenAI(
    api_key=os.environ.get("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1",
)

path = Path(__file__).parent / "assets"

spinner_html = open(path / "spinner.html").read()


system_prompt = "You are an AI coding assistant. Your task is to write single-file HTML applications based on a user's request. Only return the necessary code. Include all necessary imports and styles. You may also be asked to edit your original response."
user_prompt = "Please write a single-file HTML application to fulfill the following request.\nThe message:{user_message}\nCurrent code you have written:{code}"


def extract_html_content(text):
    """
    Extract content including HTML tags.
    """
    match = re.search(r"<!DOCTYPE html>.*?</html>", text, re.DOTALL)
    return match.group(0) if match else None


def display_in_sandbox(code):
    encoded_html = base64.b64encode(code.encode("utf-8")).decode("utf-8")
    data_uri = f"data:text/html;charset=utf-8;base64,{encoded_html}"
    return f'<iframe src="{data_uri}" width="100%" height="600px"></iframe>'


def generate(user_message: tuple[int, np.ndarray], history: list[dict], code: str):
    yield AdditionalOutputs(history, spinner_html)

    text = groq_client.audio.transcriptions.create(
        file=("audio-file.mp3", audio_to_bytes(user_message)),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
    ).text

    user_msg_formatted = user_prompt.format(user_message=text, code=code)
    history.append({"role": "user", "content": user_msg_formatted})

    response = client.chat.completions.create(
        model="Meta-Llama-3.1-70B-Instruct",
        messages=history,  # type: ignore
        temperature=0.1,
        top_p=0.1,
    )

    output = response.choices[0].message.content
    html_code = extract_html_content(output)
    history.append({"role": "assistant", "content": output})
    yield AdditionalOutputs(history, html_code)


CodeHandler = ReplyOnPause(generate)  # type: ignore
