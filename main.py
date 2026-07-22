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
    p = argparse.ArgumentParser()
    p.add_argument("--step", choices=STEPS, default="all")
    p.add_argument("--limit", type=int, default=5)
    return p.parse_args()

def is_demo():
    return os.getenv("RUN_MODE", "demo").lower() == "demo"

def step_sheet(spreadsheet_id):
    print("[1/5] Таблица")
    usernames = load_blogger_usernames(spreadsheet_id)
    print(f"  {len(usernames)} блогеров")
    cache.save("usernames", usernames)
    return usernames

def step_collect(usernames, limit, demo):
    print("[2/5] Сбор профилей")
    if demo:
        profiles = cache.load_fixture("profiles")[:limit]
        print(f"  demo: {len(profiles)} профилей")
    else:
        profiles = collect_all(usernames[:limit])
    cache.save("profiles", profiles)
    return profiles

def step_portrait(profiles, demo):
    print("[3/5] Портрет")
    if demo:
        try:
            portrait = build_portrait(profiles)
        except Exception:
            portrait = cache.load_fixture("portrait")
            print("  demo: fixture")
        else:
            print("  LLM")
    else:
        portrait = build_portrait(profiles)
    cache.save("portrait", portrait)
    return portrait

def step_discover(portrait, usernames, demo):
    print("[4/5] Поиск новых")
    if demo:
        try:
            candidates = discover_bloggers(portrait, usernames, demo=True)
        except Exception:
            candidates = cache.load_fixture("candidates")
            print("  demo: fixture")
        else:
            print("  LLM")
    else:
        candidates = discover_bloggers(portrait, usernames, demo=False)
    print(f"  {len(candidates)} кандидатов")
    cache.save("candidates", candidates)
    return candidates

def step_offers(portrait, candidates, demo):
    print("[5/5] Офферы")
    if demo:
        try:
            offers = generate_all_offers(portrait, candidates)
        except Exception:
            offers = cache.load_fixture("offers")
            print("  demo: fixture")
        else:
            print("  LLM")
    else:
        offers = generate_all_offers(portrait, candidates)
    print(f"  {len(offers)} сообщений")
    cache.save("offers", offers)
    return offers

def save_result(mode, profiles, portrait, candidates, offers):
    OUTPUT_DIR.mkdir(exist_ok=True)
    result = {
        "mode": mode,
        "source_profiles": profiles,
        "portrait": portrait,
        "new_candidates": candidates,
        "offers": offers,
    }
    path = OUTPUT_DIR / "latest_run.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nГотово: {path}")

def main():
    load_dotenv()
    args = parse_args()
    demo = is_demo()

    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise SystemExit("SPREADSHEET_ID не задан в .env")

    if demo:
        print("demo — профили из fixtures, анализ и офферы через LLM\n")

    usernames = profiles = portrait = candidates = offers = None
    step = args.step

    if step in ("sheet", "all"):
        usernames = step_sheet(spreadsheet_id)
    else:
        usernames = cache.load("usernames")

    if step in ("collect", "all"):
        profiles = step_collect(usernames, args.limit, demo)
    elif step != "sheet":
        profiles = cache.load("profiles")

    if step in ("portrait", "all"):
        profiles = profiles or cache.load("profiles")
        portrait = step_portrait(profiles, demo)
    elif step in ("discover", "offers"):
        portrait = cache.load("portrait")

    if step in ("discover", "all"):
        portrait = portrait or cache.load("portrait")
        candidates = step_discover(portrait, usernames, demo)
    elif step == "offers":
        candidates = cache.load("candidates")

    if step in ("offers", "all"):
        portrait = portrait or cache.load("portrait")
        candidates = candidates or cache.load("candidates")
        offers = step_offers(portrait, candidates, demo)

    if step == "all":
        profiles = profiles or cache.load("profiles")
        save_result("demo" if demo else "live", profiles, portrait, candidates, offers)

if __name__ == "__main__":
    main()
