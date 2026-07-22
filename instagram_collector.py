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
    source: str = "unknown"

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
            time.sleep(1)

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

def collect_all(usernames: list[str]) -> list[dict]:
    results = []
    for u in usernames:
        print(f"  → @{u}")
        results.append(collect_profile(u).to_dict())
        time.sleep(2)

    missing = [p["username"] for p in results if p["source"] == "missing"]
    if missing:
        print(
            f"\n[!] Не удалось собрать {len(missing)} профилей: {missing}\n"
            f"    Заполни data/manual_profile_notes.json (см. example) и перезапусти collect."
        )
    return results
