from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
import json
import sqlite3
import time
from typing import Any

from servicebridge.local_runtime.models import LocalModel
from servicebridge.local_runtime.runtime import HardwareProfile, detect_hardware


class FitStatus(str, Enum):
    SAFE = "SAFE"
    TIGHT = "TIGHT"
    BLOCKED = "BLOCKED"


class WorkClass(str, Enum):
    TINY = "tiny"
    STANDARD = "standard"
    HEAVY = "heavy"


@dataclass(frozen=True)
class MemoryPolicy:
    minimum_ram_reserve_gb: float = 2.5
    minimum_vram_reserve_gb: float = 1.0
    ram_reserve_fraction: float = 0.15
    vram_reserve_fraction: float = 0.12
    tight_margin_gb: float = 1.0

    def reserves(self, hw: HardwareProfile) -> tuple[float, float]:
        total_ram = float(hw.ram_gb or 0.0)
        total_vram = float(hw.gpu_vram_gb or 0.0)
        ram = max(self.minimum_ram_reserve_gb, total_ram * self.ram_reserve_fraction)
        vram = (
            max(self.minimum_vram_reserve_gb, total_vram * self.vram_reserve_fraction)
            if total_vram > 0
            else 0.0
        )
        return round(ram, 2), round(vram, 2)


@dataclass(frozen=True)
class ResourceRequest:
    capability: str
    work_class: WorkClass = WorkClass.STANDARD
    ram_gb: float = 0.0
    vram_gb: float = 0.0
    prefer_gpu: bool = True
    allow_cpu_fallback: bool = True
    model_id: str = ""
    requester: str = ""


@dataclass(frozen=True)
class AdmissionDecision:
    status: FitStatus
    capability: str
    model_id: str
    use_gpu: bool
    ram_required_gb: float
    vram_required_gb: float
    ram_available_after_reserve_gb: float
    vram_available_after_reserve_gb: float
    reason: str
    unload_candidates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class ReservationStore:
    """Persistent memory leases shared by all Forge clients."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                capability TEXT NOT NULL,
                model_id TEXT NOT NULL,
                ram_gb REAL NOT NULL,
                vram_gb REAL NOT NULL,
                last_used REAL NOT NULL,
                unloadable INTEGER NOT NULL,
                metadata_json TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "ReservationStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def reserve(
        self,
        reservation_id: str,
        *,
        owner: str,
        capability: str,
        model_id: str,
        ram_gb: float,
        vram_gb: float,
        unloadable: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now = time.time()
        with self.db:
            self.db.execute(
                """
                INSERT INTO reservations
                (reservation_id, owner, capability, model_id, ram_gb, vram_gb,
                 last_used, unloadable, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reservation_id) DO UPDATE SET
                    owner=excluded.owner,
                    capability=excluded.capability,
                    model_id=excluded.model_id,
                    ram_gb=excluded.ram_gb,
                    vram_gb=excluded.vram_gb,
                    last_used=excluded.last_used,
                    unloadable=excluded.unloadable,
                    metadata_json=excluded.metadata_json
                """,
                (
                    reservation_id,
                    owner,
                    capability,
                    model_id,
                    float(ram_gb),
                    float(vram_gb),
                    now,
                    1 if unloadable else 0,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )

    def touch(self, reservation_id: str) -> None:
        with self.db:
            self.db.execute(
                "UPDATE reservations SET last_used=? WHERE reservation_id=?",
                (time.time(), reservation_id),
            )

    def release(self, reservation_id: str) -> None:
        with self.db:
            self.db.execute(
                "DELETE FROM reservations WHERE reservation_id=?",
                (reservation_id,),
            )

    def list(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT * FROM reservations ORDER BY last_used DESC"
        ).fetchall()
        return [
            {
                "reservation_id": row["reservation_id"],
                "owner": row["owner"],
                "capability": row["capability"],
                "model_id": row["model_id"],
                "ram_gb": float(row["ram_gb"]),
                "vram_gb": float(row["vram_gb"]),
                "last_used": float(row["last_used"]),
                "unloadable": bool(row["unloadable"]),
                "metadata": json.loads(row["metadata_json"]),
            }
            for row in rows
        ]

    def totals(self, *, exclude_owner: str = "") -> tuple[float, float]:
        rows = self.list()
        if exclude_owner:
            rows = [x for x in rows if x["owner"] != exclude_owner]
        return (
            sum(float(x["ram_gb"]) for x in rows),
            sum(float(x["vram_gb"]) for x in rows),
        )

    def unload_candidates(self, required_vram_gb: float) -> list[str]:
        rows = [
            x for x in self.list()
            if x["unloadable"] and float(x["vram_gb"]) > 0
        ]
        rows.sort(key=lambda x: x["last_used"])
        freed = 0.0
        result = []
        for row in rows:
            result.append(str(row["reservation_id"]))
            freed += float(row["vram_gb"])
            if freed >= float(required_vram_gb):
                break
        return result


def _artifact_size_gb(path: str) -> float:
    root = Path(path).expanduser()
    if not root.exists():
        return 0.0
    if root.is_file():
        return root.stat().st_size / (1024**3)
    total = 0
    for item in root.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total / (1024**3)


def estimate_model_memory(model: LocalModel, *, work_class: WorkClass) -> tuple[float, float]:
    """
    Conservative default estimate when a model profile has not been benchmarked.

    Explicit min_ram_gb/min_vram_gb always win. File size is used only as a
    fallback estimate. Forge should replace these with measured peaks after
    successful runs.
    """
    disk = _artifact_size_gb(model.path)
    context_overhead = {
        WorkClass.TINY: 0.35,
        WorkClass.STANDARD: 0.75,
        WorkClass.HEAVY: 1.5,
    }[work_class]

    ram = float(model.min_ram_gb or 0.0)
    vram = float(model.min_vram_gb or 0.0)

    if ram <= 0:
        ram = max(0.75, disk * 1.15 + context_overhead)
    if vram <= 0 and model.kind in {"vision", "image", "video"}:
        # A local media/VLM model with no benchmark is treated conservatively;
        # callers can still choose CPU only where the worker supports it.
        vram = max(0.0, disk * 0.75)

    return round(ram, 2), round(vram, 2)


class MemoryAdmissionController:
    def __init__(
        self,
        reservations: ReservationStore,
        *,
        policy: MemoryPolicy | None = None,
    ):
        self.reservations = reservations
        self.policy = policy or MemoryPolicy()

    def budget(self, hardware: HardwareProfile | None = None) -> dict[str, Any]:
        hw = hardware or detect_hardware()
        reserve_ram, reserve_vram = self.policy.reserves(hw)
        leased_ram, leased_vram = self.reservations.totals()

        observed_ram_free = float(
            hw.ram_available_gb
            if hw.ram_available_gb is not None
            else hw.ram_gb or 0.0
        )
        observed_vram_free = float(
            hw.gpu_vram_free_gb
            if hw.gpu_vram_free_gb is not None
            else hw.gpu_vram_gb or 0.0
        )

        # Live free memory already reflects real processes; reservations protect
        # against concurrent Forge jobs that have been admitted but are not yet
        # reflected in OS/GPU telemetry.
        usable_ram = max(0.0, observed_ram_free - reserve_ram)
        usable_vram = max(0.0, observed_vram_free - reserve_vram)

        return {
            "hardware": hw.to_dict(),
            "reserve_ram_gb": round(reserve_ram, 2),
            "reserve_vram_gb": round(reserve_vram, 2),
            "leased_ram_gb": round(leased_ram, 2),
            "leased_vram_gb": round(leased_vram, 2),
            "usable_ram_gb": round(usable_ram, 2),
            "usable_vram_gb": round(usable_vram, 2),
            "pressure": self._pressure(usable_ram, usable_vram, hw),
        }

    @staticmethod
    def _pressure(
        usable_ram: float,
        usable_vram: float,
        hw: HardwareProfile,
    ) -> str:
        ram_total = float(hw.ram_gb or 0)
        vram_total = float(hw.gpu_vram_gb or 0)
        ram_ratio = usable_ram / ram_total if ram_total else 1.0
        vram_ratio = usable_vram / vram_total if vram_total else 1.0
        ratio = min(ram_ratio, vram_ratio)
        if ratio < 0.08:
            return "critical"
        if ratio < 0.22:
            return "constrained"
        return "normal"

    def assess(
        self,
        request: ResourceRequest,
        *,
        hardware: HardwareProfile | None = None,
    ) -> AdmissionDecision:
        hw = hardware or detect_hardware()
        budget = self.budget(hw)
        ram_available = float(budget["usable_ram_gb"])
        vram_available = float(budget["usable_vram_gb"])

        ram_need = max(0.0, float(request.ram_gb))
        vram_need = max(0.0, float(request.vram_gb)) if request.prefer_gpu else 0.0

        ram_ok = ram_need <= ram_available
        gpu_ok = vram_need <= vram_available if vram_need > 0 else True

        if ram_ok and gpu_ok:
            margin = min(
                ram_available - ram_need,
                (vram_available - vram_need) if vram_need else ram_available - ram_need,
            )
            status = (
                FitStatus.TIGHT
                if margin < self.policy.tight_margin_gb
                else FitStatus.SAFE
            )
            return AdmissionDecision(
                status=status,
                capability=request.capability,
                model_id=request.model_id,
                use_gpu=bool(vram_need > 0),
                ram_required_gb=ram_need,
                vram_required_gb=vram_need,
                ram_available_after_reserve_gb=ram_available,
                vram_available_after_reserve_gb=vram_available,
                reason=(
                    "Fits with limited headroom."
                    if status == FitStatus.TIGHT
                    else "Fits within current memory budget and reserved headroom."
                ),
            )

        if ram_ok and not gpu_ok and request.allow_cpu_fallback:
            return AdmissionDecision(
                status=FitStatus.TIGHT,
                capability=request.capability,
                model_id=request.model_id,
                use_gpu=False,
                ram_required_gb=ram_need,
                vram_required_gb=0.0,
                ram_available_after_reserve_gb=ram_available,
                vram_available_after_reserve_gb=vram_available,
                reason=(
                    "GPU memory is insufficient; admit only through a CPU/offload "
                    "worker that supports this model."
                ),
                unload_candidates=tuple(
                    self.reservations.unload_candidates(vram_need - vram_available)
                ),
            )

        needed_vram = max(0.0, vram_need - vram_available)
        return AdmissionDecision(
            status=FitStatus.BLOCKED,
            capability=request.capability,
            model_id=request.model_id,
            use_gpu=bool(vram_need > 0),
            ram_required_gb=ram_need,
            vram_required_gb=vram_need,
            ram_available_after_reserve_gb=ram_available,
            vram_available_after_reserve_gb=vram_available,
            reason=(
                "Request would violate Forge memory headroom. Unload idle workers, "
                "choose a smaller model, lower context/resolution, or use a deterministic fallback."
            ),
            unload_candidates=tuple(
                self.reservations.unload_candidates(needed_vram)
            ),
        )

    def assess_model(
        self,
        model: LocalModel,
        *,
        capability: str,
        work_class: WorkClass = WorkClass.STANDARD,
        requester: str = "",
        hardware: HardwareProfile | None = None,
        allow_cpu_fallback: bool = True,
    ) -> AdmissionDecision:
        ram, vram = estimate_model_memory(model, work_class=work_class)
        return self.assess(
            ResourceRequest(
                capability=capability,
                work_class=work_class,
                ram_gb=ram,
                vram_gb=vram,
                prefer_gpu=vram > 0,
                allow_cpu_fallback=allow_cpu_fallback,
                model_id=model.model_id,
                requester=requester,
            ),
            hardware=hardware,
        )


def choose_model(
    models: list[LocalModel],
    controller: MemoryAdmissionController,
    *,
    capability: str,
    work_class: WorkClass = WorkClass.STANDARD,
    requester: str = "",
    hardware: HardwareProfile | None = None,
) -> tuple[LocalModel | None, AdmissionDecision | None]:
    """
    Choose the highest-quality SAFE model, then a TIGHT model.

    BLOCKED models are never selected. This makes the memory gate authoritative
    instead of advisory.
    """
    ranked = sorted(models, key=lambda x: x.quality_rank, reverse=True)
    tight: tuple[LocalModel, AdmissionDecision] | None = None

    for model in ranked:
        decision = controller.assess_model(
            model,
            capability=capability,
            work_class=work_class,
            requester=requester,
            hardware=hardware,
        )
        if decision.status == FitStatus.SAFE:
            return model, decision
        if decision.status == FitStatus.TIGHT and tight is None:
            tight = (model, decision)

    return tight if tight is not None else (None, None)
