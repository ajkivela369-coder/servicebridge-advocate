from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from servicebridge.local_runtime.models import LocalModel, LocalModelCatalog


@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    kind: str
    expected_path: str
    quality_rank: int
    min_ram_gb: float
    min_vram_gb: float
    purpose: str
    policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "kind": self.kind,
            "expected_path": self.expected_path,
            "quality_rank": self.quality_rank,
            "min_ram_gb": self.min_ram_gb,
            "min_vram_gb": self.min_vram_gb,
            "purpose": self.purpose,
            "policy": self.policy,
        }


def load_profiles(path: str | Path = "config/forge_model_profiles.json") -> list[ModelProfile]:
    data = json.loads(Path(path).read_text())
    return [ModelProfile(**row) for row in data.get("profiles", [])]


def staged_profile_status(
    path: str | Path = "config/forge_model_profiles.json",
) -> list[dict[str, Any]]:
    rows = []
    for profile in load_profiles(path):
        expected = Path(profile.expected_path).expanduser()
        row = profile.to_dict()
        row["installed"] = expected.exists()
        row["status"] = "INSTALLED" if expected.exists() else "STAGED_MISSING"
        rows.append(row)
    return rows


def register_present_profiles(
    catalog_path: str | Path,
    profiles_path: str | Path = "config/forge_model_profiles.json",
) -> list[str]:
    catalog = LocalModelCatalog(catalog_path)
    registered = []
    for profile in load_profiles(profiles_path):
        path = Path(profile.expected_path).expanduser()
        if not path.exists():
            continue
        catalog.add(
            LocalModel(
                model_id=profile.profile_id,
                kind=profile.kind,
                path=str(path),
                quality_rank=profile.quality_rank,
                min_ram_gb=profile.min_ram_gb,
                min_vram_gb=profile.min_vram_gb,
                notes=profile.purpose,
            ),
            replace=True,
        )
        registered.append(profile.profile_id)
    return registered
