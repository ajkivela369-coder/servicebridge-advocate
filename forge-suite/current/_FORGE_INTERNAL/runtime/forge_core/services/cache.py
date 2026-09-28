from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


def stable_hash(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def cache_dir(key: str) -> Path:
    path = CACHE / key
    path.mkdir(parents=True, exist_ok=True)
    return path
