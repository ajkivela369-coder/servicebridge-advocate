from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def build_command(input_path: Path, output_dir: Path, modality: str, fast: bool, device: str | None, roi_subset: list[str]) -> list[str]:
    task = "total_mr" if modality.upper() == "MR" else "total"
    cmd = [
        "TotalSegmentator",
        "-i", str(input_path),
        "-o", str(output_dir),
        "--task", task,
    ]
    if fast:
        cmd.append("--fast")
    if device:
        cmd += ["--device", device]
    if roi_subset:
        cmd += ["--roi_subset", *roi_subset]
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Run TotalSegmentator locally and package masks for MedForge."
    )
    parser.add_argument("input", help="NIfTI file, DICOM folder, or DICOM ZIP")
    parser.add_argument("--output", default="medforge_segmentations")
    parser.add_argument("--modality", choices=["CT", "MR"], default="CT")
    parser.add_argument("--fast", action="store_true", help="Use TotalSegmentator fast mode")
    parser.add_argument("--device", choices=["cpu", "gpu", "mps"], default=None)
    parser.add_argument("--roi", nargs="*", default=[], help="Optional TotalSegmentator roi_subset classes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if shutil.which("TotalSegmentator") is None:
        raise SystemExit(
            "TotalSegmentator executable not found. Install with: pip install TotalSegmentator"
        )

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_command(
        input_path=input_path,
        output_dir=output_dir,
        modality=args.modality,
        fast=args.fast,
        device=args.device,
        roi_subset=args.roi,
    )
    print("Running:", " ".join(cmd))
    if args.dry_run:
        return

    subprocess.run(cmd, check=True)
    masks = sorted(str(p.name) for p in output_dir.glob("*.nii.gz"))
    manifest = {
        "app": "MedForge local segmentation worker",
        "engine": "TotalSegmentator",
        "modality": args.modality,
        "task": "total_mr" if args.modality == "MR" else "total",
        "status": "DERIVED / UNREVIEWED segmentation",
        "mask_count": len(masks),
        "masks": masks,
        "note": (
            "These masks are derived segmentation data, not source imaging or a diagnosis. "
            "Review anatomy before using masks in an evidence or mechanism visualization."
        ),
    }
    (output_dir / "medforge-segmentation-manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
