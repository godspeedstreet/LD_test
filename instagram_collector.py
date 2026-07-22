"""
Сбор публичных данных профиля: био, число подписчиков, подписи к последним постам.

ВАЖНОЕ ОГРАНИЧЕНИЕ (см. README, раздел "Ограничения"):
У Instagram нет официального публичного API для стороннего чтения чужих профилей.
instaloader обращается к тем же эндпоинтам, что и веб-версия сайта, без логина —
это работает нестабильно: Instagram агрессивно рейт-лимитит анонимные запросы
и может начать возвращать 401/429 уже после нескольких профилей подряд,
особенно с облачных IP (как раз наш случай — виртуальная машина).

Поэтому модуль устроен так:
1. Пробует получить данные автоматически через instaloader.
2. Если получить не удалось — не падает, а помечает профиль как "требует
   ручного заполнения" и продолжает работу с остальными.
3. Данные, которые не удалось собрать автоматически, можно один раз вручную
   вписать в data/manual_profile_notes.json (по 2-3 строки текста — что видно
   на скриншоте профиля) — и при повторном запуске инструмент сначала
   проверяет этот кэш, и только потом идёт в сеть.

Это осознанный компромисс между "красиво заявить, что всё скрапится само"
и "показать рабочий пайплайн, который не разваливается на первом же баге
чужого API". В проде на этом месте стоял бы платный скрапер (Apify, Bright
Data) с ротацией прокси — но это уже вопрос бюджета, а не архитектуры.
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

MANUAL_CACHE_PATH = Path(__file__).parent / "data" / "manual_profile_notes.json"


@dataclass
class ProfileData:
    username: str
    bio: str = ""
    followers: int | None = None
    recent_captions: list[str] | None = None
    source: str = "unknown"  # "instaloader" | "manual" | "missing"

    def to_dict(self):
        return asdict(self)


def _load_manual_cache() -> dict:
    if MANUAL_CACHE_PATH.exists():
        return json.loads(MANUAL_CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _fetch_via_instaloader(username: str) -> ProfileData | None:
    try:
        import instaloader
    except ImportError:
        return None

    try:
        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
            quiet=True,
        )
        profile = instaloader.Profile.from_username(loader.context, username)
        captions = []
        for i, post in enumerate(profile.get_posts()):
            if i >= 5:
                break
            if post.caption:
                captions.append(post.caption[:300])
            time.sleep(1)  # пауза между постами, чтобы меньше палиться перед рейт-лимитом
        return ProfileData(
            username=username,
            bio=profile.biography or "",
            followers=profile.followers,
            recent_captions=captions,
            source="instaloader",
        )
    except Exception:
        return None


def collect_profile(username: str) -> ProfileData:
    """Пытается собрать данные профиля: сначала ручной кэш, потом instaloader."""
    manual_cache = _load_manual_cache()
    if username in manual_cache:
        entry = manual_cache[username]
        return ProfileData(
            username=username,
            bio=entry.get("bio", ""),
            followers=entry.get("followers"),
            recent_captions=entry.get("recent_captions", []),
            source="manual",
        )

    result = _fetch_via_instaloader(username)
    if result:
        return result

    return ProfileData(username=username, source="missing")


def collect_all(usernames: list[str]) -> list[ProfileData]:
    results = []
    for u in usernames:
        results.append(collect_profile(u))
    missing = [p.username for p in results if p.source == "missing"]
    if missing:
        print(
            f"[!] Не удалось автоматически собрать данные для {len(missing)} профилей: {missing}\n"
            f"    Впиши по ним 2-3 строки в {MANUAL_CACHE_PATH.name} (формат см. в data/manual_profile_notes.example.json) "
            f"и перезапусти — они возьмутся из кэша."
        )
    return results
