from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .runtime import HardwareProfile


@dataclass(frozen=True)
class LocalModel:
    model_id: str
    kind: str
    path: str
    format: str = "unknown"
    quality_rank: int = 0
    min_ram_gb: float = 0.0
    min_vram_gb: float = 0.0
    sha256: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LocalModelCatalog:
    """
    Registry of model files already present on the machine.

    Creditless Mode never downloads a model implicitly. A model enters this
    catalog only after the user/admin has placed it on disk.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"models": []}, indent=2))

    def list(self) -> list[LocalModel]:
        data = json.loads(self.path.read_text() or "{}")
        return [LocalModel(**x) for x in data.get("models", [])]

    def save(self, models: list[LocalModel]) -> None:
        self.path.write_text(
            json.dumps({"models": [x.to_dict() for x in models]}, indent=2, sort_keys=True)
        )

    def add(self, model: LocalModel, *, replace: bool = False) -> None:
        models = self.list()
        existing = next((x for x in models if x.model_id == model.model_id), None)
        if existing and not replace:
            raise ValueError(f"Model already registered: {model.model_id}")
        models = [x for x in models if x.model_id != model.model_id]
        models.append(model)
        models.sort(key=lambda x: (x.kind, -x.quality_rank, x.model_id))
        self.save(models)

    def verify(self, model_id: str) -> dict[str, Any]:
        model = next((x for x in self.list() if x.model_id == model_id), None)
        if model is None:
            raise KeyError(model_id)
        path = Path(model.path).expanduser()
        exists = path.exists() and path.is_file()
        digest = ""
        hash_match = None
        if exists and model.sha256:
            digest = file_sha256(path)
            hash_match = digest.lower() == model.sha256.lower()
        return {
            "model_id": model_id,
            "exists": exists,
            "path": str(path),
            "sha256": digest,
            "hash_match": hash_match,
        }

    def compatible(
        self,
        kind: str,
        hardware: HardwareProfile,
    ) -> list[LocalModel]:
        out = []
        for model in self.list():
            if model.kind != kind:
                continue
            if not Path(model.path).expanduser().exists():
                continue
            if hardware.ram_gb is not None and hardware.ram_gb < model.min_ram_gb:
                continue
            # min_vram_gb=0 means CPU execution is acceptable.
            if model.min_vram_gb > 0:
                if hardware.gpu_vram_gb is None or hardware.gpu_vram_gb < model.min_vram_gb:
                    continue
            out.append(model)
        out.sort(key=lambda x: x.quality_rank, reverse=True)
        return out

    def best(self, kind: str, hardware: HardwareProfile) -> LocalModel | None:
        compatible = self.compatible(kind, hardware)
        return compatible[0] if compatible else None


def file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with open(Path(path), "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def conservative_profile_guidance(hardware: HardwareProfile) -> dict[str, str]:
    """
    Generic guidance rather than model-brand promises.

    Actual fit depends on architecture, quantization, context length and
    runtime overhead, so this intentionally stays conservative.
    """
    if hardware.gpu_vram_gb is not None and hardware.gpu_vram_gb >= 16:
        text = "Prefer medium local models; larger quantized models may fit after testing."
        image = "Local image generation and some local video workflows are realistic."
    elif hardware.gpu_vram_gb is not None and hardware.gpu_vram_gb >= 8:
        text = "Prefer small/medium quantized local models."
        image = "Local image generation is practical; video generation should use lightweight profiles."
    elif hardware.ram_gb is not None and hardware.ram_gb >= 16:
        text = "Prefer small quantized CPU models; expect slower generation."
        image = "Use deterministic rendering; treat heavy generation as optional."
    else:
        text = "Use tiny/local specialist models and deterministic fallbacks."
        image = "Prioritize FFmpeg/source-locked workflows over generative media."

    return {
        "text": text,
        "media": image,
        "rule": "A missing or oversized model must degrade locally; it must not trigger paid fallback in Creditless Mode.",
    }
