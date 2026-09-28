from __future__ import annotations

import argparse
import json
from pathlib import Path

from servicebridge.local_runtime.media import run_command, still_to_video_command


def write_ppm(path: Path, width: int, height: int) -> None:
    """Generate a deterministic source frame with no imaging dependency."""
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            r = 18 + ((x * 37) // max(1, width - 1))
            g = 28 + ((y * 63) // max(1, height - 1))
            b = 34 + (((x + y) * 41) // max(1, width + height - 2))
            pixels.extend((r % 256, g % 256, b % 256))
    path.write_bytes(header + bytes(pixels))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        default="config/recovery/representative_project.json",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project_path = Path(args.project)
    payload = json.loads(project_path.read_text())
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = out.with_suffix(".ppm")
    write_ppm(frame, int(payload["width"]), int(payload["height"]))

    command = still_to_video_command(
        frame,
        out,
        duration=float(payload["duration_seconds"]),
        width=int(payload["width"]),
        height=int(payload["height"]),
        fps=int(payload["fps"]),
    )
    run_command(command)
    if not out.is_file() or out.stat().st_size <= 0:
        raise RuntimeError("Recovery render did not create a non-empty MP4.")
    print(json.dumps({
        "project_id": payload["project_id"],
        "output": str(out),
        "bytes": out.stat().st_size,
        "rendered": True,
    }, indent=2))


if __name__ == "__main__":
    main()
