from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def still_to_video_command(
    image_path: str | Path,
    output_path: str | Path,
    *,
    duration: float = 5.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> list[str]:
    image_path = str(Path(image_path))
    output_path = str(Path(output_path))
    return [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf",
        (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
        ),
        "-r", str(int(fps)),
        "-t", f"{float(duration):.3f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path,
    ]


def concat_command(concat_file: str | Path, output_path: str | Path) -> list[str]:
    return [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(Path(concat_file)),
        "-c", "copy",
        str(Path(output_path)),
    ]


def run_command(command: list[str], timeout: float = 600.0) -> subprocess.CompletedProcess:
    exe = command[0]
    if shutil.which(exe) is None:
        raise RuntimeError(f"Required local executable is not installed: {exe}")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
