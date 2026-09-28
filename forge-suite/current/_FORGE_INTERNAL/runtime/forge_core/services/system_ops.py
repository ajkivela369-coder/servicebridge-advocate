from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from forge_base.bundle import create as create_bundle, verify as verify_bundle

ROOT = Path(__file__).resolve().parents[2]


def forge_home() -> Path:
    return Path(os.environ.get("FORGE_HOME") or (Path.home() / "Forge")).expanduser().resolve()


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except OSError:
                pass
    except OSError:
        pass
    return total


def status() -> dict:
    home = forge_home()
    home.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(home)
    areas = {}
    for name in ("models", "cache", "downloads", "vault", "projects", "backups", "exports"):
        p = home / name
        areas[name] = {
            "path": str(p),
            "exists": p.exists(),
            "bytes": _dir_size(p),
        }
    backups = []
    bdir = home / "backups"
    if bdir.exists():
        try:
            for p in sorted((x for x in bdir.rglob("*.zip") if x.is_file()), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                backups.append({"name": p.name, "path": str(p), "bytes": p.stat().st_size, "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")})
        except OSError:
            pass
    return {
        "forge_home": str(home),
        "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
        "areas": areas,
        "cache_health": {
            "cache_dir": (home / "cache").exists(),
            "downloads_dir": (home / "downloads").exists(),
            "models_dir": (home / "models").exists(),
            "retained_bytes": areas["cache"]["bytes"] + areas["downloads"]["bytes"] + areas["models"]["bytes"],
        },
        "recent_backups": backups,
        "desktop_controls": str(home / "Forge Setup and Repair.cmd"),
    }


def backup(include_models: bool = False) -> dict:
    home = forge_home()
    outdir = home / "backups" / "workspace"
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = outdir / f"Forge-Recovery-{stamp}.zip"
    result = create_bundle(out, include_models=include_models)
    result["verification"] = verify_bundle(out)
    return result


def open_desktop_controls() -> dict:
    home = forge_home()
    candidates = [
        home / "Forge Setup and Repair.cmd",
        ROOT / "installer_gui.py",
    ]
    target = next((p for p in candidates if p.exists()), None)
    if target is None:
        raise FileNotFoundError("Forge Setup and Repair launcher was not found. Re-run the Forge installer to recreate it.")
    if os.name != "nt":
        return {"ok": False, "supported": False, "target": str(target), "message": "Desktop controls launch is Windows-only."}
    if target.suffix.lower() == ".cmd":
        subprocess.Popen(["cmd.exe", "/c", "start", "", str(target)], cwd=str(home), creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    else:
        subprocess.Popen([sys.executable, str(target)], cwd=str(ROOT), creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    return {"ok": True, "supported": True, "target": str(target)}
