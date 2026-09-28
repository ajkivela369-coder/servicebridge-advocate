from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "learning" / "learning_manifest.json"
REGISTRY = ROOT / "forge_base" / "feature_registry.json"

def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def feature(feature_id: str):
    for item in manifest().get("features", []):
        if item.get("id") == feature_id:
            return item
    return None

def coverage():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    required = [f["id"] for f in reg.get("features", []) if f.get("learning_required", True)]
    taught = {f.get("id") for f in manifest().get("features", [])}
    covered = [fid for fid in required if fid in taught]
    missing = [fid for fid in required if fid not in taught]
    pct = round((len(covered) / len(required) * 100), 1) if required else 100.0
    return {"ok": not missing, "required": len(required), "covered": len(covered), "missing": missing, "coverage_percent": pct, "release": manifest().get("release")}
