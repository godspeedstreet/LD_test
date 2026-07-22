import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data" / "cache"
FIXTURES_DIR = Path(__file__).parent / "data" / "fixtures"

def save(name: str, data) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def load(name: str):
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Нет кэша {path}. Сначала запусти предыдущий шаг.")
    return json.loads(path.read_text(encoding="utf-8"))

def load_fixture(name: str):
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Нет fixture {path}")
    return json.loads(path.read_text(encoding="utf-8"))
