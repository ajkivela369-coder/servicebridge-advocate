from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def kokoro_available() -> bool:
    try:
        import kokoro  # noqa: F401
        import soundfile  # noqa: F401
        return True
    except Exception:
        return False


def generate_kokoro_local(
    text: str,
    *,
    output_wav: str | Path,
    voice: str = "af_heart",
    lang_code: str = "a",
    speed: float = 1.0,
    sample_rate: int = 24000,
) -> dict[str, Any]:
    """
    Generate Kokoro speech with network access disabled at the model-hub layer.

    Required Kokoro model/voice files must already exist in the local HF cache.
    If they are missing, the call should fail rather than download them.
    """
    if not text.strip():
        raise ValueError("text is required.")

    # Force offline behavior before importing/initializing the model pipeline.
    previous = {
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        "HF_HUB_DISABLE_TELEMETRY": os.environ.get("HF_HUB_DISABLE_TELEMETRY"),
    }
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline

        pipeline = KPipeline(lang_code=lang_code)
        chunks = []
        segment_count = 0
        for _graphemes, _phonemes, audio in pipeline(
            text,
            voice=voice,
            speed=float(speed),
        ):
            if audio is None:
                continue
            arr = np.asarray(audio, dtype=np.float32).reshape(-1)
            if arr.size:
                chunks.append(arr)
                segment_count += 1

        if not chunks:
            raise RuntimeError(
                "Kokoro produced no audio. Confirm the model and requested voice "
                "are already available in the local cache."
            )

        combined = np.concatenate(chunks)
        output = Path(output_wav)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output), combined, int(sample_rate))

        return {
            "output_path": str(output),
            "provider": "local-kokoro",
            "voice": voice,
            "lang_code": lang_code,
            "speed": float(speed),
            "sample_rate": int(sample_rate),
            "segments": segment_count,
            "network_downloads_allowed": False,
        }
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
