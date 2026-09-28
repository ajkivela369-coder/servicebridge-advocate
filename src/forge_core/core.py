from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import time
from typing import Any

from servicebridge.local_runtime import (
    AssetCache,
    JobQueue,
    LocalModelCatalog,
    RuntimeMode,
    detect_hardware,
    discover_services,
)
from servicebridge.local_runtime.workers import worker_capabilities

from .scheduler import (
    FitStatus,
    MemoryAdmissionController,
    ReservationStore,
    WorkClass,
    choose_model,
    estimate_model_memory,
)
from .vault import ForgeVault


FORGE_VERSION = "0.4.0"


CAPABILITY_SPECS: dict[str, dict[str, Any]] = {
    "reason": {
        "model_kind": "text",
        "fallback": "deterministic/template or explicit unavailable state",
    },
    "code": {
        "model_kind": "code",
        "fallback": "text model if registered; otherwise explicit unavailable state",
    },
    "vision": {
        "model_kind": "vision",
        "fallback": "manual/source-faithful review",
    },
    "transcribe": {
        "worker": "faster_whisper",
        "fallback": "manual transcript import",
    },
    "tts": {
        "workers": ["kokoro", "piper"],
        "fallback": "captions/silent render",
    },
    "embed": {
        "model_kind": "embedding",
        "fallback": "SQLite full-text search",
    },
    "search": {
        "worker": "sqlite",
        "fallback": "SQLite full-text search",
    },
    "ocr": {
        "worker": "paddleocr",
        "fallback": "embedded PDF text/manual correction",
    },
    "diagram": {
        "worker": "deterministic",
        "fallback": "deterministic SVG/scene manifest",
    },
    "image": {
        "workers": ["diffusers", "comfyui"],
        "fallback": "source-locked/deterministic illustration",
    },
    "video": {
        "workers": ["ffmpeg", "diffusers", "comfyui"],
        "fallback": "deterministic FFmpeg render",
    },
    "3d": {
        "workers": ["medforge_native3d", "blender"],
        "fallback": "native Python 3D or static geometry export",
    },
    "medical_segmentation": {
        "worker": "totalsegmentator",
        "fallback": "reviewed imported masks/manual segmentation",
    },
    "export": {
        "worker": "deterministic",
        "fallback": "local deterministic export",
    },
    "provenance": {
        "worker": "forge_vault",
        "fallback": "Forge Vault is core and has no cloud dependency",
    },
}


APP_MANIFEST = {
    "elias": {
        "name": "Elias",
        "capabilities": ["reason", "embed", "search", "ocr", "transcribe", "export", "provenance"],
    },
    "evidence_auditor": {
        "name": "Evidence Auditor",
        "capabilities": ["reason", "embed", "search", "ocr", "transcribe", "diagram", "export", "provenance"],
    },
    "medforge": {
        "name": "MedForge",
        "capabilities": ["vision", "medical_segmentation", "3d", "diagram", "video", "export", "provenance"],
    },
    "grimforge": {
        "name": "GrimForge",
        "capabilities": ["reason", "vision", "tts", "image", "video", "export", "provenance"],
    },
}


def _mode_from_env() -> RuntimeMode:
    raw = os.getenv("FORGE_MODE", "creditless").strip().lower()
    if raw in {"local", "local_only", "creditless"}:
        return RuntimeMode.CREDITLESS
    if raw == "hybrid":
        return RuntimeMode.HYBRID
    return RuntimeMode.CREDITLESS


@dataclass(frozen=True)
class ForgePaths:
    root: Path
    model_catalog: Path
    reservations: Path
    jobs: Path
    cache: Path
    vault: Path

    @classmethod
    def default(cls) -> "ForgePaths":
        root = Path(os.getenv("FORGE_DATA_ROOT", "./private_data/forge"))
        return cls(
            root=root,
            model_catalog=Path(
                os.getenv(
                    "FORGE_MODEL_CATALOG",
                    "./private_data/local_runtime/models.json",
                )
            ),
            reservations=root / "reservations.sqlite3",
            jobs=root / "jobs.sqlite3",
            cache=root / "cache",
            vault=root / "vault",
        )


class ForgeCore:
    """One backend contract shared by Elias, Evidence Auditor, MedForge and GrimForge."""

    def __init__(
        self,
        *,
        paths: ForgePaths | None = None,
        mode: RuntimeMode | None = None,
    ):
        self.paths = paths or ForgePaths.default()
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.mode = mode or _mode_from_env()

    def status(self) -> dict[str, Any]:
        hw = detect_hardware()
        with ReservationStore(self.paths.reservations) as reservations:
            controller = MemoryAdmissionController(reservations)
            budget = controller.budget(hw)
            leases = reservations.list()
        return {
            "status": "ok",
            "name": "Forge Core",
            "version": FORGE_VERSION,
            "mode": self.mode.value,
            "local_only": self.mode == RuntimeMode.CREDITLESS,
            "hardware": hw.to_dict(),
            "memory_budget": budget,
            "reservations": leases,
            "services": [x.to_dict() for x in discover_services()],
            "workers": [x.to_dict() for x in worker_capabilities()],
            "apps": self.apps(),
        }

    def apps(self) -> list[dict[str, Any]]:
        return [
            {
                "app_id": app_id,
                "name": spec["name"],
                "backend": "Forge Core",
                "required_capabilities": list(spec["capabilities"]),
            }
            for app_id, spec in APP_MANIFEST.items()
        ]

    def capability_status(self) -> list[dict[str, Any]]:
        services = {x.service_id: x for x in discover_services()}
        workers = {x.worker_id: x for x in worker_capabilities()}
        catalog = LocalModelCatalog(self.paths.model_catalog)
        hw = detect_hardware()
        models = catalog.list()

        out = []
        for capability, spec in CAPABILITY_SPECS.items():
            ready = False
            detail = ""
            model_kind = spec.get("model_kind")
            if model_kind:
                candidates = [
                    x for x in models
                    if x.kind == model_kind and Path(x.path).expanduser().exists()
                ]
                ready = bool(candidates)
                detail = (
                    f"{len(candidates)} registered local model(s)"
                    if candidates else f"no installed {model_kind} model registered"
                )
            else:
                names = []
                if spec.get("worker"):
                    names.append(spec["worker"])
                names.extend(spec.get("workers", []))
                if capability in {"diagram", "export", "provenance", "search"}:
                    ready = True
                    detail = "Forge deterministic/core worker"
                else:
                    states = []
                    for name in names:
                        if name in workers:
                            states.append(bool(workers[name].available))
                        elif name in services:
                            states.append(bool(services[name].healthy))
                    ready = any(states)
                    detail = ", ".join(names) if names else "core"

            out.append(
                {
                    "capability": capability,
                    "ready": ready,
                    "fallback": spec["fallback"],
                    "detail": detail,
                    "backend": "Forge Core",
                }
            )
        return out

    def list_models(self) -> list[dict[str, Any]]:
        catalog = LocalModelCatalog(self.paths.model_catalog)
        hw = detect_hardware()
        models = catalog.list()
        rows = []
        with ReservationStore(self.paths.reservations) as reservations:
            controller = MemoryAdmissionController(reservations)
            for model in models:
                exists = Path(model.path).expanduser().exists()
                ram, vram = estimate_model_memory(
                    model,
                    work_class=WorkClass.STANDARD,
                )
                decision = controller.assess_model(
                    model,
                    capability=model.kind,
                    work_class=WorkClass.STANDARD,
                    hardware=hw,
                ) if exists else None
                rows.append(
                    {
                        **model.to_dict(),
                        "installed": exists,
                        "estimated_ram_gb": ram,
                        "estimated_vram_gb": vram,
                        "fit": decision.status.value if decision else "MISSING",
                        "fit_reason": decision.reason if decision else "Model files not present.",
                    }
                )
        return rows

    def select_model(
        self,
        *,
        capability: str,
        work_class: WorkClass = WorkClass.STANDARD,
        requester: str,
    ) -> dict[str, Any]:
        spec = CAPABILITY_SPECS.get(capability)
        if spec is None:
            raise KeyError(f"Unknown Forge capability: {capability}")
        kind = spec.get("model_kind")
        if not kind:
            return {
                "capability": capability,
                "selected_model": None,
                "fit": "DETERMINISTIC",
                "reason": spec["fallback"],
            }

        catalog = LocalModelCatalog(self.paths.model_catalog)
        candidates = [
            x for x in catalog.list()
            if x.kind == kind and Path(x.path).expanduser().exists()
        ]
        with ReservationStore(self.paths.reservations) as reservations:
            controller = MemoryAdmissionController(reservations)
            model, decision = choose_model(
                candidates,
                controller,
                capability=capability,
                work_class=work_class,
                requester=requester,
            )
            if model is None or decision is None:
                return {
                    "capability": capability,
                    "selected_model": None,
                    "fit": FitStatus.BLOCKED.value,
                    "reason": (
                        "No installed model can be admitted under the current RAM/VRAM budget. "
                        f"Fallback: {spec['fallback']}."
                    ),
                }

            reservation_id = f"model:{requester}:{capability}"
            reservations.reserve(
                reservation_id,
                owner=requester,
                capability=capability,
                model_id=model.model_id,
                ram_gb=decision.ram_required_gb,
                vram_gb=decision.vram_required_gb if decision.use_gpu else 0.0,
                unloadable=True,
                metadata={
                    "work_class": work_class.value,
                    "fit": decision.status.value,
                    "use_gpu": decision.use_gpu,
                },
            )
            return {
                "capability": capability,
                "selected_model": model.to_dict(),
                "fit": decision.status.value,
                "decision": decision.to_dict(),
                "reservation_id": reservation_id,
            }

    def unload_model(self, reservation_id: str) -> dict[str, Any]:
        with ReservationStore(self.paths.reservations) as reservations:
            before = {x["reservation_id"] for x in reservations.list()}
            reservations.release(reservation_id)
            return {
                "released": reservation_id in before,
                "reservation_id": reservation_id,
            }

    def vault_status(self) -> dict[str, Any]:
        with ForgeVault(self.paths.vault) as vault:
            return vault.status()

    def job_status(self) -> list[dict[str, Any]]:
        queue = JobQueue(self.paths.jobs)
        try:
            rows = queue.db.execute(
                "SELECT * FROM jobs ORDER BY updated_at DESC LIMIT 100"
            ).fetchall()
            return [
                {
                    "job_id": row["job_id"],
                    "kind": row["kind"],
                    "status": row["status"],
                    "payload": __import__("json").loads(row["payload_json"]),
                    "result": __import__("json").loads(row["result_json"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]
        finally:
            queue.close()

    def cache_status(self) -> dict[str, Any]:
        with AssetCache(self.paths.cache) as cache:
            count = cache.db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            size = 0
            for path in cache.blobs.glob("*"):
                try:
                    size += path.stat().st_size
                except OSError:
                    pass
            return {
                "asset_count": int(count),
                "bytes": int(size),
                "path": str(self.paths.cache),
            }
