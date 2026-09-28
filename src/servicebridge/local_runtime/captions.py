from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap


@dataclass(frozen=True)
class CaptionCue:
    start: float
    end: float
    text: str


def seconds_to_srt_time(seconds: float) -> str:
    millis = max(0, round(float(seconds) * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def cues_to_srt(cues: list[CaptionCue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = cue.text.strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n{seconds_to_srt_time(cue.start)} --> {seconds_to_srt_time(cue.end)}\n{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def scene_narration_to_cues(
    scenes: list[dict],
    *,
    text_key: str = "narration",
    duration_key: str = "duration",
    max_chars_per_line: int = 44,
) -> list[CaptionCue]:
    """
    Deterministic scene-level captions.

    This does not claim word-level timing. It simply places each scene's known
    narration inside that scene's time window.
    """
    cursor = 0.0
    cues: list[CaptionCue] = []
    for scene in scenes:
        duration = float(scene.get(duration_key, 0) or 0)
        text = str(scene.get(text_key, "") or "").strip()
        if duration <= 0:
            continue
        if text:
            wrapped = "\n".join(
                textwrap.wrap(text, width=max(20, int(max_chars_per_line)))
            )
            cues.append(
                CaptionCue(
                    start=cursor,
                    end=cursor + duration,
                    text=wrapped,
                )
            )
        cursor += duration
    return cues


def write_srt(path: str | Path, cues: list[CaptionCue]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cues_to_srt(cues), encoding="utf-8")
    return path
