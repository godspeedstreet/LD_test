from pathlib import Path
from llm_client import chat_json

PROMPT_PATH = Path(__file__).parent / "02_discovery_prompt.md"

def _load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    return text.split("## Системный промпт", 1)[1].strip()

def discover_bloggers(portrait: dict, exclude_usernames: list[str]) -> list[dict]:
    system = _load_system_prompt()
    user = (
        f"Портрет идеального блогера:\n{portrait}\n\n"
        f"Исключи этих username (уже в базе): {exclude_usernames}\n\n"
        "Найди 3–5 новых подходящих блогеров."
    )
    result = chat_json(system, user)
    candidates = result.get("candidates", [])
    exclude = {u.lower() for u in exclude_usernames}
    return [c for c in candidates if c.get("username", "").lower() not in exclude][:5]
