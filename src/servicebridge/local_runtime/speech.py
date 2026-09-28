from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .tts import generate_kokoro_local, kokoro_available
from .workers import run_piper


def local_tts_status(*, piper_model: str | Path | None = None) -> dict[str, Any]:
    piper_model = str(piper_model or os.getenv("SERVICEBRIDGE_PIPER_MODEL", "")).strip()
    return {
        "kokoro_available": kokoro_available(),
        "piper_model_configured": bool(piper_model and Path(piper_model).expanduser().is_file()),
        "selection_order": ["kokoro", "piper"],
        "cloud_fallback": False,
    }


def generate_speech_local_auto(
    text: str,
    *,
    output_wav: str | Path,
    kokoro_voice: str = "af_heart",
    kokoro_lang_code: str = "a",
    kokoro_speed: float = 1.0,
    piper_model: str | Path | None = None,
) -> dict[str, Any]:
    """
    Local-only narration chooser.

    Try offline Kokoro first. If Kokoro is unavailable or its cached model/voice
    is missing, use a configured local Piper voice. Never calls a cloud TTS.
    """
    errors = []

    if kokoro_available():
        try:
            result = generate_kokoro_local(
                text,
                output_wav=output_wav,
                voice=kokoro_voice,
                lang_code=kokoro_lang_code,
                speed=kokoro_speed,
            )
            result["auto_selected"] = "kokoro"
            return result
        except Exception as exc:
            errors.append(f"Kokoro: {type(exc).__name__}: {exc}")

    piper_path = Path(
        str(piper_model or os.getenv("SERVICEBRIDGE_PIPER_MODEL", "")).strip()
    ).expanduser()
    if str(piper_path) not in {"", "."} and piper_path.is_file():
        try:
            output = run_piper(
                text,
                model_path=piper_path,
                output_wav=output_wav,
            )
            return {
                "output_path": str(output),
                "provider": "local-piper",
                "auto_selected": "piper",
                "network_downloads_allowed": False,
            }
        except Exception as exc:
            errors.append(f"Piper: {type(exc).__name__}: {exc}")

    raise RuntimeError(
        "No working local narration engine is configured. "
        + (" | ".join(errors) if errors else "Install/cache Kokoro or configure SERVICEBRIDGE_PIPER_MODEL.")
    )
