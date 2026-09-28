from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from servicebridge.local_runtime.archive import safe_extract_zip


def main():
    parser = argparse.ArgumentParser(
        description="Run a MedForge Blender bundle with local Blender."
    )
    parser.add_argument("bundle", help="medforge-blender-bundle.zip")
    parser.add_argument("--output-dir", default="./medforge_blender_output")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    blender = shutil.which("blender")
    if not blender:
        raise SystemExit("Blender is not installed or not on PATH.")

    bundle = Path(args.bundle).resolve()
    if not bundle.is_file():
        raise SystemExit(f"Bundle not found: {bundle}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="medforge-blender-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(bundle) as zf:
            safe_extract_zip(zf, root)

        script = root / "blender_medforge_scene.py"
        scene = root / "scene.json"
        command = [
            blender,
            "--background",
            "--python",
            str(script),
            "--",
            "--scene",
            str(scene),
        ]
        if args.render:
            command.append("--render")
        subprocess.run(command, check=True)

        generated = root / "outputs"
        if generated.is_dir():
            for path in generated.iterdir():
                if path.is_file():
                    shutil.copy2(path, output_dir / path.name)

    print(f"Blender outputs copied to: {output_dir}")


if __name__ == "__main__":
    main()
