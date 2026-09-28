from __future__ import annotations
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def check():
    registry = json.loads((HERE / "feature_registry.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / "learning" / "learning_manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "missing": ["learning_manifest.json"], "required": 0, "covered": 0, "coverage_percent": 0.0}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = [f["id"] for f in registry.get("features", []) if f.get("learning_required", True)]
    entries = {f.get("id"): f for f in manifest.get("features", [])}
    missing=[]; incomplete=[]
    for fid in required:
        item=entries.get(fid)
        if not item:
            missing.append(fid); continue
        lesson=item.get("lesson") or {}
        if not lesson.get("summary") or not item.get("build_story") or not item.get("workspace_url") or not item.get("concepts"):
            incomplete.append(fid)
    covered=len(required)-len(missing)-len(incomplete)
    pct=round((covered/len(required)*100),1) if required else 100.0
    return {"ok":not missing and not incomplete,"required":len(required),"covered":covered,"missing":missing,"incomplete":incomplete,"coverage_percent":pct}

if __name__ == "__main__":
    result=check(); print(json.dumps(result,indent=2)); raise SystemExit(0 if result["ok"] else 1)
