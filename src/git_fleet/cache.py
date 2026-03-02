from __future__ import annotations

import json
import os
import time
from pathlib import Path

_CACHE_DIR = Path.home() / ".cache" / "git-fleet"
_TTL_SECONDS = 5 * 60  # 5 minutes


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def load_cache(key: str) -> object | None:
    """Load cached data if it exists and is fresh."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        if time.time() - mtime > _TTL_SECONDS:
            return None
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_cache(key: str, data: object) -> None:
    """Save data to cache."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def clear_cache() -> None:
    """Remove all cached files."""
    if _CACHE_DIR.exists():
        for f in _CACHE_DIR.iterdir():
            if f.suffix == ".json":
                f.unlink(missing_ok=True)
