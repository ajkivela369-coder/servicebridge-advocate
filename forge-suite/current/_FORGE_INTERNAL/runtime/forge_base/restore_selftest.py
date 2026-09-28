from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json, os, subprocess, sys
from forge_base.forge_base import forge_home, init, report

root = forge_home()
init(root)
r = report(root)
checks = {
    "forge_home_exists": Path(r["forge_home"]).exists(),
    "manifest_written": (Path(r["forge_home"])/"manifests"/"doctor-latest.json").exists(),
    "python_ok": True,
    "ffmpeg_ready": next((t["installed"] for t in r["tools"] if t["id"]=="ffmpeg"), False),
}
probe = Path(root)/"tmp"/"restore-selftest.txt"
probe.write_text("forge restore self-test\n")
checks["workspace_writable"] = probe.exists()
try: probe.unlink()
except OSError: pass
print(json.dumps({"ok": all(v for k,v in checks.items() if k not in {"ffmpeg_ready"}), "checks": checks, "forge_home": str(root)}, indent=2))
