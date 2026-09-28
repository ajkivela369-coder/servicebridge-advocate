from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import textwrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from servicebridge.local_runtime.captions import scene_narration_to_cues, write_srt
from servicebridge.local_runtime.render import LocalRenderPlan, LocalSceneAsset, render_plan
from servicebridge.local_runtime.speech import generate_speech_local_auto


def _source_image_from_payload(source_media: dict[str, Any] | None) -> Image.Image | None:
    if not source_media:
        return None
    data_uri = str(source_media.get("data_uri", "") or "")
    if not data_uri.startswith("data:image/") or "," not in data_uri:
        return None
    try:
        raw = base64.b64decode(data_uri.split(",", 1)[1])
        return Image.open(BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _text(draw, xy, text, *, font, fill, max_width_chars=55, spacing=7):
    lines = []
    for paragraph in str(text or "").splitlines():
        wrapped = textwrap.wrap(paragraph, width=max_width_chars) or [""]
        lines.extend(wrapped)
    draw.multiline_text(xy, "\n".join(lines), font=font, fill=fill, spacing=spacing)


def make_scene_card(
    scene: dict[str, Any],
    output_path: str | Path,
    *,
    source_image: Image.Image | None = None,
    width: int = 1280,
    height: int = 720,
) -> Path:
    """Create a deterministic local scene card; never calls an image provider."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if source_image is not None:
        background = ImageOps.fit(source_image.copy(), (width, height), method=Image.Resampling.LANCZOS)
    else:
        background = Image.new("RGB", (width, height), (17, 18, 17))
        draw = ImageDraw.Draw(background)
        # Deterministic abstract battlefield depth; no generated/copyrighted imagery.
        for y in range(height):
            p = y / max(1, height - 1)
            shade = int(10 + 25 * (1 - p))
            draw.line((0, y, width, y), fill=(shade + 8, shade + 3, shade))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, width, height), fill=(5, 7, 7, 92))
    od.rectangle((0, int(height * 0.54), width, height), fill=(5, 6, 6, 205))
    od.rectangle((0, 0, width, 54), fill=(7, 10, 9, 215))
    background = Image.alpha_composite(background.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(background)
    font = ImageFont.load_default()
    title = str(scene.get("title", "Untitled scene"))
    act = str(scene.get("act", ""))
    scene_id = str(scene.get("id", scene.get("scene_id", "")))
    visual = str(scene.get("visual", ""))
    narration = str(scene.get("narration", ""))

    draw.text((28, 18), f"{scene_id} · {act} · LOCAL DETERMINISTIC FORGE", font=font, fill=(226, 196, 128, 255))
    _text(draw, (50, int(height * 0.59)), title.upper(), font=font, fill=(255, 244, 216, 255), max_width_chars=50)
    _text(draw, (50, int(height * 0.66)), visual, font=font, fill=(208, 205, 196, 255), max_width_chars=82, spacing=5)
    if narration:
        _text(draw, (50, int(height * 0.82)), narration, font=font, fill=(229, 204, 150, 255), max_width_chars=88, spacing=5)

    draw.text(
        (28, height - 24),
        "LOCAL ANIMATIC · scene card / source-locked visual · not a generative final shot",
        font=font,
        fill=(160, 160, 152, 255),
    )
    background.convert("RGB").save(output, quality=92)
    return output


def prepare_grimforge_local_assets(
    episode: dict[str, Any],
    *,
    output_dir: str | Path,
    source_media: dict[str, Any] | None = None,
    use_local_tts: bool = True,
    piper_model: str | Path | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    source_image = _source_image_from_payload(source_media)
    scenes = list(episode.get("scenes", []))
    if not scenes:
        raise ValueError("Episode contains no scenes.")

    scene_assets = []
    tts_errors = []
    for index, scene in enumerate(scenes, start=1):
        image = make_scene_card(
            scene,
            out / f"scene_{index:03d}.png",
            source_image=source_image,
        )
        audio = ""
        narration = " ".join(
            x for x in [
                str(scene.get("narration", "") or "").strip(),
                str(scene.get("dialogue", "") or "").strip(),
            ]
            if x
        )
        if use_local_tts and narration:
            wav = out / f"scene_{index:03d}.wav"
            try:
                generate_speech_local_auto(
                    narration,
                    output_wav=wav,
                    piper_model=piper_model,
                )
                audio = str(wav)
            except Exception as exc:
                tts_errors.append(f'{scene.get("id", index)}: {type(exc).__name__}: {exc}')

        duration = float(scene.get("duration", 6) or 6)
        scene_assets.append(
            LocalSceneAsset(
                scene_id=str(scene.get("id", f"S{index:02d}")),
                image_path=str(image),
                duration=max(1.0, duration),
                audio_path=audio,
            )
        )

    cue_source = [
        {
            "duration": float(scene.get("duration", 6) or 6),
            "narration": " ".join(
                x for x in [
                    str(scene.get("narration", "") or "").strip(),
                    str(scene.get("dialogue", "") or "").strip(),
                ] if x
            ),
        }
        for scene in scenes
    ]
    captions = write_srt(
        out / "captions.srt",
        scene_narration_to_cues(cue_source),
    )

    return {
        "scenes": scene_assets,
        "captions_path": str(captions),
        "tts_errors": tts_errors,
        "source_locked_image_used": source_image is not None,
    }


def render_grimforge_local(
    episode: dict[str, Any],
    *,
    output_dir: str | Path,
    source_media: dict[str, Any] | None = None,
    use_local_tts: bool = True,
    piper_model: str | Path | None = None,
    fps: int = 30,
    width: int = 1280,
    height: int = 720,
) -> dict[str, Any]:
    """Always-available local episode renderer: cards/source + TTS/silence + captions + FFmpeg."""
    out = Path(output_dir)
    prepared = prepare_grimforge_local_assets(
        episode,
        output_dir=out,
        source_media=source_media,
        use_local_tts=use_local_tts,
        piper_model=piper_model,
    )
    final = out / "grimforge-creditless.mp4"
    plan = LocalRenderPlan(
        title=str(episode.get("title", "GrimForge local episode")),
        output_path=str(final),
        scenes=prepared["scenes"],
        subtitles_path=prepared["captions_path"],
        width=int(width),
        height=int(height),
        fps=int(fps),
        audio_lufs=-16,
    )
    render_plan(plan)
    return {
        "output_path": str(final),
        "scene_count": len(prepared["scenes"]),
        "tts_errors": prepared["tts_errors"],
        "source_locked_image_used": prepared["source_locked_image_used"],
        "used_cloud": False,
        "render_mode": "Deterministic Forge",
    }
