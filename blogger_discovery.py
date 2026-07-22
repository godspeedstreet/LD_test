import re
import time
from pathlib import Path
from llm_client import chat_json

PROMPT_PATH = Path(__file__).parent / "02_discovery_prompt.md"

MIN_FOLLOWERS = 5_000
MAX_FOLLOWERS = 150_000
CANDIDATE_LIMIT = 5

def _load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    return text.split("## Системный промпт", 1)[1].strip()

def _normalize_keywords(portrait: dict) -> list[str]:
    keywords = portrait.get("search_keywords") or portrait.get("recurring_themes") or []
    clean = []
    for kw in keywords:
        tag = re.sub(r"[^\wа-яА-ЯёЁ]", "", str(kw).lstrip("#").strip())
        if tag and tag not in clean:
            clean.append(tag)
    return clean[:5]

def _discover_via_hashtags(keywords: list[str], exclude: set[str]) -> list[dict]:
    import instaloader

    loader = instaloader.Instaloader(quiet=True)
    found: dict[str, dict] = {}

    for kw in keywords:
        print(f"  → хэштег #{kw}")
        try:
            hashtag = instaloader.Hashtag.from_name(loader.context, kw)
            for post in hashtag.get_posts():
                username = post.owner_username
                if username in exclude or username in found:
                    continue

                profile = post.owner_profile
                followers = profile.followers or 0
                if not (MIN_FOLLOWERS <= followers <= MAX_FOLLOWERS):
                    continue

                found[username] = {
                    "username": username,
                    "platform": "instagram",
                    "profile_url": f"https://www.instagram.com/{username}/",
                    "followers_estimate": str(followers),
                    "bio": profile.biography or "",
                    "found_via_hashtag": kw,
                    "why_fit": "",
                }

                if len(found) >= CANDIDATE_LIMIT * 3:
                    break
        except Exception as e:
            print(f"    [!] хэштег #{kw} недоступен: {e}")

        time.sleep(2)
        if len(found) >= CANDIDATE_LIMIT * 3:
            break

    return list(found.values())

def _enrich_with_llm(portrait: dict, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []

    system = _load_system_prompt()
    user = (
        f"Портрет идеального блогера:\n{portrait}\n\n"
        f"Вот реальные найденные кандидаты (не выдумывай новых):\n{candidates}\n\n"
        "Выбери 3–5 лучших, дополни why_fit для каждого. "
        "Верни JSON: {\"candidates\": [...]}"
    )
    result = chat_json(system, user)
    return result.get("candidates", candidates)[:CANDIDATE_LIMIT]

def discover_bloggers(portrait: dict, exclude_usernames: list[str], use_llm_rank: bool = True) -> list[dict]:
    keywords = _normalize_keywords(portrait)
    if not keywords:
        raise RuntimeError("В портрете нет search_keywords — нечем искать.")

    exclude = {u.lower() for u in exclude_usernames}
    raw_candidates = _discover_via_hashtags(keywords, exclude)

    if not raw_candidates:
        raise RuntimeError(
            "Не найдено кандидатов через Instagram. "
            "Попробуй позже или проверь search_keywords в portrait.json."
        )

    if use_llm_rank:
        return _enrich_with_llm(portrait, raw_candidates)

    for c in raw_candidates[:CANDIDATE_LIMIT]:
        c["why_fit"] = (
            f"Найден по хэштегу #{c['found_via_hashtag']}, "
            f"{c['followers_estimate']} подписчиков, подходит под портрет."
        )
    return raw_candidates[:CANDIDATE_LIMIT]
