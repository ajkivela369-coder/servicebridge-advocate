from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS = {
    "mode": "creditless",
    "forge_core_url": "http://127.0.0.1:8765",
    "model_policy": "balanced",
    "storage_root": "./private_data/forge",
    "backup_root": "./private_data/forge_backups",
    "auto_unload_idle_models": True,
    "idle_unload_minutes": 10,
}


class ForgeSettings:
    def __init__(self, path: str | Path = "./private_data/forge/settings.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        data = dict(DEFAULT_SETTINGS)
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text() or "{}")
                if isinstance(loaded, dict):
                    data.update(loaded)
            except Exception:
                pass
        if data["mode"] not in {"creditless", "hybrid"}:
            data["mode"] = "creditless"
        return data

    def save(self, settings: dict[str, Any]) -> dict[str, Any]:
        data = dict(DEFAULT_SETTINGS)
        data.update(settings)
        if data["mode"] not in {"creditless", "hybrid"}:
            raise ValueError("Forge Launcher supports only creditless or hybrid mode.")
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))
        return data
