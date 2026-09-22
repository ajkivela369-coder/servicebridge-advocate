from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable, Literal

Stage = Literal[
    "planned",
    "preview",
    "generated",
    "rendered",
    "qc_passed",
    "export_ready",
]

RightsBasis = Literal[
    "owned",
    "licensed",
    "permission",
    "public_domain",
    "generated_original",
    "unknown",
]


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    kind: Literal["video", "tts", "vision", "music", "render", "captions"]
    connected: bool = False
    max_width: int | None = None
    max_height: int | None = None
    supported_fps: tuple[int, ...] = ()
    supports_seed: bool = False
    supports_reference_images: bool = False
    supports_voice_lock: bool = False
    notes: str = ""


@dataclass
class RenderSettings:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    video_bitrate_mbps: int = 16
    audio_lufs: int = -16
    quality: Literal["highest_available", "balanced", "fast_preview"] = "highest_available"


@dataclass
class RenderJob:
    job_id: str
    app: str
    title: str
    stage: Stage = "planned"
    rights_basis: RightsBasis = "unknown"
    attribution: str = ""
    source_asset_ids: list[str] = field(default_factory=list)
    character_asset_ids: list[str] = field(default_factory=list)
    set_asset_ids: list[str] = field(default_factory=list)
    selected_take_ids: list[str] = field(default_factory=list)
    settings: RenderSettings = field(default_factory=RenderSettings)
    provider_ids: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QCResult:
    passed: bool
    checks: dict[str, bool]
    warnings: tuple[str, ...]


def select_provider(
    providers: Iterable[ProviderCapabilities],
    kind: str,
    settings: RenderSettings,
) -> ProviderCapabilities | None:
    candidates = [p for p in providers if p.connected and p.kind == kind]
    if not candidates:
        return None

    def rank(p: ProviderCapabilities) -> tuple[int, int, int]:
        pixels = (p.max_width or 0) * (p.max_height or 0)
        fps_fit = int(not p.supported_fps or settings.fps in p.supported_fps)
        refs = int(p.supports_reference_images)
        return fps_fit, pixels, refs

    return max(candidates, key=rank)


def run_qc(
    *,
    rights_basis: RightsBasis,
    has_video: bool,
    has_audio: bool,
    caption_overflow: bool = False,
    audio_clipping: bool = False,
    black_frames: bool = False,
    continuity_warnings: int = 0,
) -> QCResult:
    checks = {
        "rights_known": rights_basis != "unknown",
        "video_present": has_video,
        "audio_present": has_audio,
        "captions_fit": not caption_overflow,
        "audio_not_clipped": not audio_clipping,
        "no_black_frames": not black_frames,
        "continuity_clear": continuity_warnings == 0,
    }
    warnings: list[str] = []
    if rights_basis == "unknown":
        warnings.append("Rights provenance is unresolved.")
    if not has_video:
        warnings.append("No rendered video is present.")
    if not has_audio:
        warnings.append("No final audio mix is present.")
    if caption_overflow:
        warnings.append("Caption overflow detected.")
    if audio_clipping:
        warnings.append("Audio clipping detected.")
    if black_frames:
        warnings.append("Black frames detected.")
    if continuity_warnings:
        warnings.append(f"{continuity_warnings} continuity warning(s) remain.")

    return QCResult(
        passed=all(checks.values()),
        checks=checks,
        warnings=tuple(warnings),
    )


def can_mark_export_ready(job: RenderJob, qc: QCResult) -> bool:
    return job.stage in {"rendered", "qc_passed"} and qc.passed
