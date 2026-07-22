from pathlib import Path
from llm_client import chat_json

PROMPT_PATH = Path(__file__).parent / "03_offer_prompt.md"

def _load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    return text.split("## Системный промпт", 1)[1].strip()

def generate_offer(portrait: dict, candidate: dict) -> dict:
    system = _load_system_prompt()
    user = (
        f"Портрет нашего идеального партнёра:\n{portrait}\n\n"
        f"Данные блогера:\n{candidate}\n\n"
        "Напиши персональный оффер."
    )
    return chat_json(system, user)

def generate_all_offers(portrait: dict, candidates: list[dict]) -> list[dict]:
    return [generate_offer(portrait, c) for c in candidates]
