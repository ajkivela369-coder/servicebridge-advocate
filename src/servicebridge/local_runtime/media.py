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



def mux_audio_command(
    video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    *,
    audio_lufs: int = -16,
) -> list[str]:
    """Mux local narration/audio into a video and normalize perceived loudness."""
    return [
        "ffmpeg",
        "-y",
        "-i", str(Path(video_path)),
        "-i", str(Path(audio_path)),
        "-filter:a", f"loudnorm=I={int(audio_lufs)}:TP=-1.5:LRA=11",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(Path(output_path)),
    ]


def burn_subtitles_command(
    video_path: str | Path,
    subtitles_path: str | Path,
    output_path: str | Path,
) -> list[str]:
    """Burn SRT/ASS captions with FFmpeg's subtitles filter."""
    subtitle = str(Path(subtitles_path)).replace("\\", "/").replace(":", "\\:")
    return [
        "ffmpeg",
        "-y",
        "-i", str(Path(video_path)),
        "-vf", f"subtitles='{subtitle}'",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-c:a", "copy",
        str(Path(output_path)),
    ]


def image_sequence_command(
    frame_pattern: str,
    output_path: str | Path,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> list[str]:
    """Turn numbered local frames into a normal H.264 MP4."""
    return [
        "ffmpeg",
        "-y",
        "-framerate", str(int(fps)),
        "-i", frame_pattern,
        "-vf",
        (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
        ),
        "-c:v", "libx264",
        "-r", str(int(fps)),
        "-pix_fmt", "yuv420p",
        str(Path(output_path)),
    ]



def scene_video_command(
    image_path: str | Path,
    output_path: str | Path,
    *,
    duration: float,
    audio_path: str | Path | None = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    audio_lufs: int = -16,
) -> list[str]:
    """
    Build one scene segment with an audio stream every time.

    If narration/audio is absent, FFmpeg generates silence so every segment has
    compatible video+audio streams for deterministic concatenation.
    """
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(Path(image_path))]
    if audio_path:
        cmd += ["-i", str(Path(audio_path))]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]

    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    )
    cmd += [
        "-vf", video_filter,
        "-filter:a", f"loudnorm=I={int(audio_lufs)}:TP=-1.5:LRA=11",
        "-r", str(int(fps)),
        "-t", f"{float(duration):.3f}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(Path(output_path)),
    ]
    return cmd



def video_clip_scene_command(
    video_path: str | Path,
    output_path: str | Path,
    *,
    duration: float,
    audio_path: str | Path | None = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    audio_lufs: int = -16,
) -> list[str]:
    """
    Normalize an existing local video clip into a Forge scene segment.

    This is the handoff used for Blender-rendered anatomy/mechanism clips and
    other locally generated video. Existing clip audio is intentionally ignored;
    the render plan supplies narration/audio explicitly or receives silence.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str(Path(video_path)),
    ]
    if audio_path:
        cmd += ["-i", str(Path(audio_path))]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]

    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    )
    cmd += [
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vf", video_filter,
        "-filter:a", f"loudnorm=I={int(audio_lufs)}:TP=-1.5:LRA=11",
        "-r", str(int(fps)),
        "-t", f"{float(duration):.3f}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(Path(output_path)),
    ]
    return cmd



def probe_media_duration(path: str | Path, timeout: float = 15.0) -> float | None:
    """Return local media duration in seconds using ffprobe when available."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [
                exe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(Path(path)),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        value = float(proc.stdout.strip())
        return value if value > 0 else None
    except Exception:
        return None
