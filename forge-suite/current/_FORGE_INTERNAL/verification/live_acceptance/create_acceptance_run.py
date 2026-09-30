#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

VISUAL_CATEGORIES = [
    "brief_fidelity",
    "coherence",
    "continuity",
    "geometry_anatomy_integrity",
    "composition",
    "lighting",
    "motion_camera",
    "artifact_control",
    "contamination_control",
    "product_suitability",
]

NARRATOR_CATEGORIES = [
    "intelligibility",
    "naturalness",
    "prosody_emphasis",
    "pacing",
    "pronunciation",
    "accent_consistency",
    "noise_artifacts",
    "clipping_distortion",
    "emotional_fit",
    "long_form_comfort",
]

def git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None

def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser(description="Create a Forge live-acceptance evidence packet.")
    p.add_argument("--product", required=True, help="e.g. GrimForge or MedForge")
    p.add_argument("--route", default="", help="e.g. 3d, 2.5d, 2d, narrator, windows")
    p.add_argument("--engine", default="", help="real engine/provider used")
    p.add_argument("--model", default="", help="model/workflow identifier")
    p.add_argument("--voice", default="", help="voice identifier when relevant")
    p.add_argument("--output-dir", default="acceptance-results")
    args = p.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}-{uuid.uuid4().hex[:8]}"
    root = Path(args.output_dir) / run_id
    (root / "artifacts").mkdir(parents=True, exist_ok=False)

    manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "state": "pending_live_evidence",
        "product": args.product,
        "requested_route": args.route,
        "actual_route": "",
        "engine_provider": args.engine,
        "model_workflow": args.model,
        "voice": args.voice,
        "forge_commit_sha": git_sha(),
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "input_id": "",
        "prompt_or_script_id": "",
        "started_utc": "",
        "finished_utc": "",
        "runtime_seconds": None,
        "outputs": [],
        "reviewer": "",
        "reviewed_utc": "",
        "disposition": "PENDING",
        "limitations": [],
    }

    visual = {
        "scale": "1=unacceptable, 5=portfolio/production-ready",
        "threshold": {"mean_min": 4.0, "category_floor": 3, "critical_defects_max": 0},
        "scores": {k: None for k in VISUAL_CATEGORIES},
        "critical_defects": [],
        "evidence_notes": {},
        "mean_score": None,
        "pass": None,
    }

    narrator = {
        "scale": "1=unacceptable, 5=portfolio/production-ready",
        "threshold": {
            "mean_min": 4.0,
            "intelligibility_min": 4,
            "naturalness_min": 4,
            "clipping_or_dropouts_allowed": False,
        },
        "scores": {k: None for k in NARRATOR_CATEGORIES},
        "objective": {
            "sample_rate": None,
            "channels": None,
            "peak_dbfs": None,
            "clipping": None,
            "dropouts": None,
            "duration_seconds": None,
            "normalization_mastering": "",
        },
        "mean_score": None,
        "pass": None,
    }

    windows = {
        "phases": {
            "dependency_preflight": "PENDING",
            "first_install": "PENDING",
            "first_launch": "PENDING",
            "sample_state_created": "PENDING",
            "in_place_upgrade": "PENDING",
            "state_preservation": "PENDING",
            "reboot_relaunch": "PENDING",
            "optional_engine_offline": "PENDING",
            "repair_recovery": "PENDING",
            "uninstall_boundary_if_supported": "PENDING",
        },
        "preserved": {
            "forge_home": None,
            "vault": None,
            "settings": None,
            "outputs": None,
        },
        "shortcuts_correct": None,
        "core_relaunch_ok": None,
        "security_setting_disabled": False,
        "critical_defects": [],
        "pass": None,
    }

    write_json(root / "manifest.json", manifest)
    write_json(root / "visual-scorecard.json", visual)
    write_json(root / "narrator-scorecard.json", narrator)
    write_json(root / "windows-scorecard.json", windows)
    (root / "notes.md").write_text(
        "# Acceptance run notes\n\n"
        "Record observations, defects, screenshots/recordings, fixes attempted, and reviewer rationale.\n"
        "Do not put PHI, secrets, credentials, or private claimant material here.\n",
        encoding="utf-8",
    )

    print(root)
    print("Created manifest + visual, narrator and Windows scorecards. Keep generated media under artifacts/.")

if __name__ == "__main__":
    main()
