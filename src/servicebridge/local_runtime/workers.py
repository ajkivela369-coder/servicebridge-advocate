from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any
from urllib.request import Request, urlopen

from .runtime import RuntimePolicy


@dataclass(frozen=True)
class WorkerCapability:
    worker_id: str
    available: bool
    mode: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "available": self.available,
            "mode": self.mode,
            "notes": self.notes,
        }


def worker_capabilities() -> list[WorkerCapability]:
    return [
        WorkerCapability(
            "faster_whisper",
            importlib.util.find_spec("faster_whisper") is not None,
            "python-local",
            "Speech-to-text with optional CPU/GPU inference.",
        ),
        WorkerCapability(
            "piper",
            shutil.which("piper") is not None,
            "cli-local",
            "Local neural text-to-speech.",
        ),
        WorkerCapability(
            "ffmpeg",
            shutil.which("ffmpeg") is not None,
            "cli-local",
            "Deterministic audio/video assembly.",
        ),
        WorkerCapability(
            "llama_cpp",
            shutil.which("llama-server") is not None,
            "http-local",
            "Local LLM/VLM server.",
        ),
        WorkerCapability(
            "comfyui",
            False,
            "http-local",
            "Availability is determined by the runtime health check at port 8188.",
        ),
        WorkerCapability(
            "paddleocr",
            importlib.util.find_spec("paddleocr") is not None,
            "python-local",
            "Local OCR/document parsing. Pre-provision model weights for fully offline use.",
        ),
        WorkerCapability(
            "pypdf",
            importlib.util.find_spec("pypdf") is not None,
            "python-local",
            "Local embedded-text extraction from PDFs.",
        ),
        WorkerCapability(
            "diffusers",
            importlib.util.find_spec("diffusers") is not None,
            "python-local",
            "Direct local image/video pipelines when torch and local model weights are installed.",
        ),
        WorkerCapability(
            "kokoro",
            importlib.util.find_spec("kokoro") is not None,
            "python-local",
            "Higher-quality local TTS; Creditless adapter forces model-hub offline mode.",
        ),
        WorkerCapability(
            "medforge_native3d",
            all(
                importlib.util.find_spec(name) is not None
                for name in ("numpy", "matplotlib", "skimage", "scipy")
            ) and shutil.which("ffmpeg") is not None,
            "python-local",
            "No-Blender patient-space 3D mechanism rendering with Python + FFmpeg.",
        ),
    ]


def transcribe_file(
    media_path: str | Path,
    *,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
) -> dict[str, Any]:
    """
    Run faster-whisper in-process if installed.

    The model may download weights on first use unless the user points
    faster-whisper at a local model directory. The app should surface that
    distinction in Creditless Mode before first run.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install it locally or use an "
            "already-downloaded compatible model."
        ) from exc

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(str(Path(media_path)), language=language)
    rows = []
    full_text = []
    for segment in segments:
        text = segment.text.strip()
        rows.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text,
            }
        )
        if text:
            full_text.append(text)
    return {
        "language": getattr(info, "language", language),
        "duration": getattr(info, "duration", None),
        "segments": rows,
        "text": " ".join(full_text),
    }


def piper_command(
    text_file: str | Path,
    model_path: str | Path,
    output_wav: str | Path,
) -> list[str]:
    return [
        "piper",
        "--model",
        str(Path(model_path)),
        "--output_file",
        str(Path(output_wav)),
        "--input_file",
        str(Path(text_file)),
    ]


def run_piper(
    text: str,
    *,
    model_path: str | Path,
    output_wav: str | Path,
    timeout: float = 300.0,
) -> Path:
    exe = shutil.which("piper")
    if not exe:
        raise RuntimeError("Piper is not installed or not on PATH.")

    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    text_file = output_wav.with_suffix(".txt")
    text_file.write_text(text, encoding="utf-8")
    command = piper_command(text_file, model_path, output_wav)
    subprocess.run(command, check=True, timeout=timeout)
    return output_wav


class ComfyUIClient:
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8188",
        policy: RuntimePolicy | None = None,
        timeout: float = 30.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.policy = policy or RuntimePolicy()
        self.timeout = timeout
        self.policy.assert_url_allowed(self.endpoint)

    def submit(self, workflow: dict[str, Any], client_id: str = "servicebridge-local") -> dict[str, Any]:
        url = f"{self.endpoint}/prompt"
        self.policy.assert_url_allowed(url)
        payload = {"prompt": workflow, "client_id": client_id}
        req = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def history(self, prompt_id: str) -> dict[str, Any]:
        url = f"{self.endpoint}/history/{prompt_id}"
        self.policy.assert_url_allowed(url)
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))
