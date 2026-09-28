from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def mix_voice_music_command(
    narration_path: str | Path,
    music_path: str | Path,
    output_path: str | Path,
    *,
    duration: float | None = None,
    voice_lufs: int = -16,
    music_gain_db: float = -8.0,
) -> list[str]:
    """
    Mix narration with local music using sidechain compression for ducking.

    The voice is the sidechain signal; music is lowered while speech is active.
    """
    music_gain = f"volume={float(music_gain_db):.2f}dB"
    graph = (
        f"[0:a]loudnorm=I={int(voice_lufs)}:TP=-1.5:LRA=11[voice];"
        f"[1:a]{music_gain}[music];"
        "[music][voice]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=300[ducked];"
        "[voice][ducked]amix=inputs=2:normalize=0[mix]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(Path(narration_path)),
        "-stream_loop", "-1",
        "-i", str(Path(music_path)),
        "-filter_complex", graph,
        "-map", "[mix]",
        "-c:a", "aac",
        "-b:a", "192k",
    ]
    if duration is not None:
        cmd += ["-t", f"{float(duration):.3f}"]
    cmd.append(str(Path(output_path)))
    return cmd


def run_audio_mix(command: list[str], timeout: float = 600.0) -> subprocess.CompletedProcess:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required for local audio mixing.")
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
