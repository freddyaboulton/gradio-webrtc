import os
from typing import Literal

import requests


def get_hf_turn_credentials(token=None):
    if token is None:
        token = os.getenv("HF_TOKEN")
    credentials = requests.get(
        "https://freddyaboulton-turn-server-login.hf.space/credentials",
        headers={"X-HF-Access-Token": token},
    )
    if not credentials.status_code == 200:
        raise ValueError("Failed to get credentials from HF turn server")
    return {
        "iceServers": [
            {
                "urls": "turn:gradio-turn.com:80",
                **credentials.json(),
            },
        ]
    }


def get_twilio_turn_credentials(twilio_sid=None, twilio_token=None):
    try:
        from twilio.rest import Client
    except ImportError:
        raise ImportError("Please install twilio with `pip install twilio`")

    if not twilio_sid and not twilio_token:
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")

    client = Client(twilio_sid, twilio_token)

    token = client.tokens.create()

    return {
        "iceServers": token.ice_servers,
        "iceTransportPolicy": "relay",
    }


def get_turn_credentials(method: Literal["hf", "twilio"] = "hf", **kwargs):
    if method == "hf":
        return get_hf_turn_credentials(**kwargs)
    elif method == "twilio":
        return get_twilio_turn_credentials(**kwargs)
    else:
        raise ValueError("Invalid method. Must be 'hf' or 'twilio'")
