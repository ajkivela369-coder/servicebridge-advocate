from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import tempfile
from typing import Iterable

from servicebridge.local_runtime.captions import CaptionCue, write_srt
from servicebridge.local_runtime.media import probe_media_duration
from servicebridge.local_runtime.render import LocalRenderPlan, LocalSceneAsset, render_plan
from servicebridge.local_runtime.speech import generate_speech_local_auto, local_tts_status


@dataclass(frozen=True)
class WildTakeBeat:
    timestamp: str
    text: str


def parse_timestamp(value: str) -> float:
    value = value.strip()
    match = re.fullmatch(r"(?:(\d+):)?(\d{1,2})(?:\.(\d+))?", value)
    if not match:
        raise ValueError(f"Unsupported timestamp: {value}")
    minutes = int(match.group(1) or 0)
    seconds = int(match.group(2))
    fraction = float("0." + (match.group(3) or "0"))
    return minutes * 60 + seconds + fraction


def beats_to_cues(beats: Iterable[WildTakeBeat], total_duration: float) -> list[CaptionCue]:
    rows = sorted(
        [(parse_timestamp(b.timestamp), b.text.strip()) for b in beats if b.text.strip()],
        key=lambda x: x[0],
    )
    cues = []
    for index, (start, text) in enumerate(rows):
        next_start = rows[index + 1][0] if index + 1 < len(rows) else float(total_duration)
        end = min(float(total_duration), max(start + 0.8, next_start))
        if start >= total_duration:
            continue
        cues.append(CaptionCue(start=max(0.0, start), end=end, text=text))
    return cues


def render_wildtake_local(
    source_bytes: bytes,
    source_name: str,
    *,
    beats: list[WildTakeBeat],
    narration_text: str,
    output_dir: str | Path,
    use_local_tts: bool = True,
    kokoro_voice: str = "af_heart",
    piper_model: str | Path | None = None,
    fallback_duration: float | None = None,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> dict:
    """
    Produce a complete WildTake MP4 locally.

    TTS is optional: if no local narrator is configured, the clip is still
    rendered with deterministic captions and silence. No cloud provider is used.
    """
    if not source_bytes:
        raise ValueError("Source video is empty.")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    suffix = Path(source_name).suffix.lower() or ".mp4"
    source = out / f"source{suffix}"
    source.write_bytes(source_bytes)

    duration = probe_media_duration(source)
    if duration is None:
        beat_end = max([parse_timestamp(b.timestamp) for b in beats] + [0.0]) + 3.0
        duration = float(fallback_duration or max(beat_end, 5.0))

    captions = out / "captions.srt"
    write_srt(captions, beats_to_cues(beats, duration))

    narration = None
    tts_result = None
    tts_error = ""
    if use_local_tts and narration_text.strip():
        narration = out / "narration.wav"
        try:
            tts_result = generate_speech_local_auto(
                narration_text,
                output_wav=narration,
                kokoro_voice=kokoro_voice,
                piper_model=piper_model,
            )
        except Exception as exc:
            narration = None
            tts_error = f"{type(exc).__name__}: {exc}"

    final = out / "wildtake-final.mp4"
    plan = LocalRenderPlan(
        title="WildTake local render",
        output_path=str(final),
        scenes=[
            LocalSceneAsset(
                scene_id="SOURCE",
                image_path="",
                duration=float(duration),
                audio_path=str(narration) if narration else "",
                video_path=str(source),
            )
        ],
        subtitles_path=str(captions),
        width=int(width),
        height=int(height),
        fps=int(fps),
        audio_lufs=-16,
    )
    render_plan(plan)

    return {
        "output_path": str(final),
        "duration_seconds": float(duration),
        "caption_count": len(beats_to_cues(beats, duration)),
        "tts": tts_result,
        "tts_error": tts_error,
        "used_cloud": False,
        "fallback_if_tts_missing": "captions + silence",
        "local_tts_status": local_tts_status(piper_model=piper_model),
    }
