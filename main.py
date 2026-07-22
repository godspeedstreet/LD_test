import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

import cache
from sheet_reader import load_blogger_usernames
from instagram_collector import collect_all
from portrait_builder import build_portrait
from blogger_discovery import discover_bloggers
from offer_generator import generate_all_offers

OUTPUT_DIR = Path(__file__).parent / "output"

STEPS = ("sheet", "collect", "portrait", "discover", "offers", "all")

def parse_args():
    p = argparse.ArgumentParser(description="Blogger outreach pipeline")
    p.add_argument("--step", choices=STEPS, default="all")
    p.add_argument("--fixtures", action="store_true", help="Использовать готовые fixture-данные")
    p.add_argument("--limit", type=int, default=5, help="Сколько профилей из таблицы брать на collect")
    p.add_argument("--no-llm-rank", action="store_true", help="Discover без LLM-ранжирования")
    return p.parse_args()

def step_sheet(spreadsheet_id: str) -> list[str]:
    print("[sheet] Читаю Google Sheets...")
    usernames = load_blogger_usernames(spreadsheet_id)
    print(f"  найдено: {len(usernames)}")
    cache.save("usernames", usernames)
    return usernames

def step_collect(usernames: list[str], limit: int, fixtures: bool) -> list[dict]:
    print("[collect] Собираю профили...")
    if fixtures:
        profiles = cache.load_fixture("profiles")
        print(f"  fixtures: {len(profiles)} профилей")
    else:
        profiles = collect_all(usernames[:limit])
    cache.save("profiles", profiles)
    return profiles

def step_portrait(profiles: list[dict], fixtures: bool) -> dict:
    print("[portrait] Строю портрет...")
    if fixtures:
        portrait = cache.load_fixture("portrait")
        print("  fixture portrait загружен")
    else:
        portrait = build_portrait(profiles)
    cache.save("portrait", portrait)
    return portrait

def step_discover(portrait: dict, usernames: list[str], fixtures: bool, no_llm_rank: bool) -> list[dict]:
    print("[discover] Ищу новых кандидатов...")
    if fixtures:
        candidates = cache.load_fixture("candidates")
        print(f"  fixtures: {len(candidates)} кандидатов")
    else:
        candidates = discover_bloggers(
            portrait,
            usernames,
            use_llm_rank=not no_llm_rank,
        )
    cache.save("candidates", candidates)
    return candidates

def step_offers(portrait: dict, candidates: list[dict], fixtures: bool) -> list[dict]:
    print("[offers] Генерирую офферы...")
    if fixtures:
        offers = [
            {
                "username": c["username"],
                "platform": c.get("platform", "instagram"),
                "message": (
                    f"Привет, @{c['username']}! Нам очень откликается твой стиль — "
                    f"особенно {c.get('why_fit', 'подача контента')}. "
                    "Хотим предложить бартер: 1–2 вещи из новой коллекции в обмен на Stories/Reels. "
                    "Если интересно — напиши, пришлю подборку."
                ),
            }
            for c in candidates
        ]
        print(f"  fixtures: {len(offers)} офферов")
    else:
        offers = generate_all_offers(portrait, candidates)
    cache.save("offers", offers)
    return offers

def save_final_result(profiles, portrait, candidates, offers):
    OUTPUT_DIR.mkdir(exist_ok=True)
    result = {
        "portrait": portrait,
        "source_profiles_count": len(profiles),
        "new_candidates": candidates,
        "offers": offers,
    }
    path = OUTPUT_DIR / "latest_run.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Результат сохранён: {path}")

def main():
    load_dotenv()
    args = parse_args()

    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id and not args.fixtures:
        raise SystemExit("Укажи SPREADSHEET_ID в .env")

    usernames = profiles = portrait = candidates = offers = None

    if args.step in ("sheet", "all"):
        usernames = step_sheet(spreadsheet_id)
    elif args.fixtures:
        usernames = cache.load_fixture("profiles")
        usernames = [p["username"] for p in usernames]
    else:
        usernames = cache.load("usernames")

    if args.step in ("collect", "all"):
        profiles = step_collect(usernames, args.limit, args.fixtures)
    elif args.step in ("portrait", "discover", "offers"):
        profiles = cache.load_fixture("profiles") if args.fixtures else cache.load("profiles")

    if args.step in ("portrait", "all"):
        profiles = profiles or (cache.load_fixture("profiles") if args.fixtures else cache.load("profiles"))
        portrait = step_portrait(profiles, args.fixtures)
    elif args.step in ("discover", "offers"):
        portrait = cache.load_fixture("portrait") if args.fixtures else cache.load("portrait")

    if args.step in ("discover", "all"):
        portrait = portrait or (cache.load_fixture("portrait") if args.fixtures else cache.load("portrait"))
        candidates = step_discover(portrait, usernames, args.fixtures, args.no_llm_rank)
    elif args.step == "offers":
        candidates = cache.load_fixture("candidates") if args.fixtures else cache.load("candidates")

    if args.step in ("offers", "all"):
        portrait = portrait or (cache.load_fixture("portrait") if args.fixtures else cache.load("portrait"))
        candidates = candidates or (cache.load_fixture("candidates") if args.fixtures else cache.load("candidates"))
        offers = step_offers(portrait, candidates, args.fixtures)

    if args.step == "all":
        profiles = profiles or cache.load("profiles")
        save_final_result(profiles, portrait, candidates, offers)

if __name__ == "__main__":
    main()
