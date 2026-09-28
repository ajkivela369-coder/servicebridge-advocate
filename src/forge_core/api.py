from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:
    raise RuntimeError(
        "Forge Core API requires: pip install 'servicebridge-advocate[api]'"
    ) from exc

from .core import FORGE_VERSION, ForgeCore
from .scheduler import WorkClass


class SelectModelBody(BaseModel):
    capability: str
    work_class: WorkClass = WorkClass.STANDARD
    requester: str


class UnloadModelBody(BaseModel):
    reservation_id: str


app = FastAPI(
    title="Forge Core",
    version=FORGE_VERSION,
    description="One local-first backend for Elias, Evidence Auditor, MedForge, and GrimForge.",
)


@app.get("/health")
@app.get("/v1/status")
def status():
    return ForgeCore().status()


@app.get("/v1/hardware")
def hardware():
    state = ForgeCore().status()
    return {
        "hardware": state["hardware"],
        "memory_budget": state["memory_budget"],
    }


@app.get("/v1/capabilities")
def capabilities():
    return {"capabilities": ForgeCore().capability_status()}


@app.get("/v1/models")
def models():
    return {"models": ForgeCore().list_models()}


@app.post("/v1/models/select")
def select_model(body: SelectModelBody):
    try:
        return ForgeCore().select_model(
            capability=body.capability,
            work_class=body.work_class,
            requester=body.requester,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/models/unload")
def unload_model(body: UnloadModelBody):
    return ForgeCore().unload_model(body.reservation_id)


@app.get("/v1/apps")
def apps():
    return {"apps": ForgeCore().apps()}


@app.get("/v1/vault/status")
def vault_status():
    return ForgeCore().vault_status()


@app.get("/v1/jobs")
def jobs():
    return {"jobs": ForgeCore().job_status()}


@app.get("/v1/cache/status")
def cache_status():
    return ForgeCore().cache_status()


@app.get("/v1/backup/status")
def backup_status():
    return {
        "configured": False,
        "verified_restore": False,
        "detail": "Backup/recovery verification is not complete yet in v0.4.",
    }


@app.post("/v1/backup/verify")
def backup_verify():
    return {
        "verified": False,
        "detail": "A backup is not marked PASS until a clean restore rebuilds and renders a representative project.",
    }


@app.post("/v1/recovery/drill")
def recovery_drill():
    return {
        "started": False,
        "detail": "Use the Forge disaster-recovery runner; destructive environment changes are not triggered from the API.",
    }
