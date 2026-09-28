from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


DEFAULT_REQUIREMENTS = [
    "portfolio/evidence-auditor/legacy-streamlit/requirements.txt",
    "portfolio/grimforge-studio/requirements.txt",
    "apps/grimforge-war-theater/requirements.txt",
    "apps/wildtake-streamlit/requirements.txt",
    "apps/medforge-imaging-studio/requirements.txt",
    "apps/medforge-build-lab/requirements.txt",
    "apps/forge-systems-lab/requirements.txt",
]


def run(args):
    print("+", " ".join(str(x) for x in args))
    subprocess.run([str(x) for x in args], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare a local Python wheelhouse for Creditless/offline reinstall."
    )
    parser.add_argument("--output", default="./wheelhouse")
    parser.add_argument("--with-whisper", action="store_true")
    parser.add_argument("--with-ocr", action="store_true")
    parser.add_argument("--with-kokoro", action="store_true")
    parser.add_argument("--with-diffusers", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    # Build the repository itself as a wheel so core code can be restored
    # without contacting an index.
    run([sys.executable, "-m", "pip", "wheel", str(root), "--wheel-dir", str(output)])

    for rel in DEFAULT_REQUIREMENTS:
        req = root / rel
        if req.is_file():
            run([
                sys.executable, "-m", "pip", "download",
                "--dest", str(output),
                "-r", str(req),
            ])

    optional = []
    if args.with_whisper:
        optional.append("faster-whisper")
    if args.with_ocr:
        optional.append("paddleocr")
    if args.with_kokoro:
        optional += ["kokoro", "soundfile"]
    if args.with_diffusers:
        optional += ["diffusers", "transformers", "accelerate"]

    if optional:
        run([
            sys.executable, "-m", "pip", "download",
            "--dest", str(output),
            *optional,
        ])

    print(f"Wheelhouse ready: {output}")
    print("Copy this directory into the same folder as the repo/offline pack before reinstalling.")


if __name__ == "__main__":
    main()
