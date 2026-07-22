import json
import os
from openai import OpenAI

def chat(system: str, user: str, json_mode: bool = False) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Нет OPENAI_API_KEY в .env")

    client = OpenAI(api_key=api_key)
    kwargs = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content

def chat_json(system: str, user: str) -> dict:
    return json.loads(chat(system, user, json_mode=True))
