import json
import os
from pathlib import Path
from dotenv import load_dotenv

from sheet_reader import load_blogger_usernames
from instagram_collector import collect_all
from portrait_builder import build_portrait
from blogger_discovery import discover_bloggers
from offer_generator import generate_all_offers

OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = Path(__file__).parent / "data"

def load_demo_profiles() -> list[dict]:
    return json.loads((DATA_DIR / "demo_profiles.json").read_text(encoding="utf-8"))

def main():
    load_dotenv()
    mode = os.getenv("RUN_MODE", "demo")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")

    usernames = load_blogger_usernames(spreadsheet_id)
    print(f"[1/5] Загружено блогеров из таблицы: {len(usernames)}")

    if mode == "demo":
        profiles = [p for p in load_demo_profiles() if p["username"] in usernames][:10]
        print(f"[2/5] DEMO: используются сохранённые профили ({len(profiles)})")
    else:
        profiles = [p.to_dict() for p in collect_all(usernames[:15])]
        print(f"[2/5] Собраны данные профилей: {len(profiles)}")

    portrait = build_portrait(profiles)
    print("[3/5] Портрет идеального блогера построен")

    candidates = discover_bloggers(portrait, usernames)
    print(f"[4/5] Найдено новых кандидатов: {len(candidates)}")

    offers = generate_all_offers(portrait, candidates)
    print(f"[5/5] Сгенерировано офферов: {len(offers)}")

    result = {
        "portrait": portrait,
        "source_profiles_count": len(profiles),
        "new_candidates": candidates,
        "offers": offers,
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_json = OUTPUT_DIR / "latest_run.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nГотово → {out_json}")

if __name__ == "__main__":
    main()
