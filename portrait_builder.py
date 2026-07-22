from pathlib import Path
from llm_client import chat_json

PROMPT_PATH = Path(__file__).parent / "01_portrait_prompt.md"

def _load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    return text.split("## Системный промпт", 1)[1].split("## User-промпт", 1)[0].strip()

def _format_profiles(profiles: list[dict]) -> str:
    blocks = []
    for p in profiles:
        caps = p.get("recent_captions") or []
        caps_text = "\n".join(f"- {c}" for c in caps) if caps else "нет данных"
        blocks.append(
            f"### @{p['username']}\n"
            f"Био: {p.get('bio') or 'нет данных'}\n"
            f"Подписчики: {p.get('followers') or 'нет данных'}\n"
            f"Последние подписи:\n{caps_text}\n---"
        )
    return "\n\n".join(blocks)

def build_portrait(profiles: list[dict]) -> dict:
    usable = [p for p in profiles if p.get("bio") or p.get("recent_captions")]
    if not usable:
        raise RuntimeError("Нет данных профилей для анализа. Заполни manual cache или collect.")

    system = _load_system_prompt()
    user = (
        f"Вот данные по {len(usable)} блогерам:\n\n"
        f"{_format_profiles(usable)}\n\n"
        "Проанализируй группу и верни JSON-портрет."
    )
    return chat_json(system, user)
