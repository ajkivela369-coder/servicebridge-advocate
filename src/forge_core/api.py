from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:
    raise RuntimeError(
        "Forge Core API requires: pip install 'servicebridge-advocate[api]'"
    ) from exc

from .core import FORGE_VERSION, ForgeCore
from .sdk import ForgeSDK
from .scheduler import WorkClass


class SelectModelBody(BaseModel):
    capability: str
    work_class: WorkClass = WorkClass.STANDARD
    requester: str


class UnloadModelBody(BaseModel):
    reservation_id: str


class ReasonBody(BaseModel):
    app_id: str
    instructions: str
    input: str
    work_class: WorkClass = WorkClass.STANDARD


class VisionBody(BaseModel):
    app_id: str
    image_data_uri: str
    instructions: str
    question: str
    work_class: WorkClass = WorkClass.STANDARD


class EmbedBody(BaseModel):
    app_id: str
    texts: list[str]


class TTSBody(BaseModel):
    app_id: str
    text: str
    output_wav: str
    piper_model: str | None = None
    kokoro_voice: str = "af_heart"


class TranscribeBody(BaseModel):
    app_id: str
    media_path: str
    model_size: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = None


class OCRBody(BaseModel):
    app_id: str
    path: str


class VideoBody(BaseModel):
    app_id: str
    plan: dict


class VaultBytesBody(BaseModel):
    app_id: str
    original_name: str
    data_b64: str
    mime_type: str = ""
    metadata: dict = {}
    role: str = "source"
    locator: str = ""


class IngestBody(BaseModel):
    app_id: str
    original_name: str
    data_b64: str
    mime_type: str = ""
    metadata: dict = {}


class SearchBody(BaseModel):
    app_id: str
    query: str
    limit: int = 12


class BackupVerifyBody(BaseModel):
    pack_path: str


class RecoveryDrillBody(BaseModel):
    pack_path: str
    network_isolation_confirmed: bool = False
    primary_executable: str = "ollama"


def _sdk(app_id: str) -> ForgeSDK:
    # The Forge daemon must execute jobs locally. Never recurse back into its
    # own HTTP surface even if FORGE_CORE_URL is present in the environment.
    return ForgeSDK(app_id=app_id, core_url="")


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
    from .recovery import load_recovery_status
    report = ForgeCore().paths.root / "recovery" / "latest.json"
    return load_recovery_status(report)


@app.post("/v1/backup/verify")
def backup_verify(body: BackupVerifyBody):
    from servicebridge.local_runtime.offline import verify_offline_pack
    return verify_offline_pack(body.pack_path)


@app.post("/v1/recovery/drill")
def recovery_drill(body: RecoveryDrillBody):
    from .recovery import run_recovery_drill
    report_path = ForgeCore().paths.root / "recovery" / "latest.json"
    report = run_recovery_drill(
        body.pack_path,
        report_path=report_path,
        primary_executable=body.primary_executable,
        network_isolation_confirmed=body.network_isolation_confirmed,
    )
    return report.to_dict()



@app.post("/v1/reason")
def reason(body: ReasonBody):
    return _sdk(body.app_id).reason(
        body.instructions,
        body.input,
        work_class=body.work_class,
    )


@app.post("/v1/vision")
def vision(body: VisionBody):
    return _sdk(body.app_id).vision(
        image_data_uri=body.image_data_uri,
        instructions=body.instructions,
        question=body.question,
        work_class=body.work_class,
    )


@app.post("/v1/embed")
def embed(body: EmbedBody):
    return _sdk(body.app_id).embed(body.texts)


@app.post("/v1/transcribe")
def transcribe(body: TranscribeBody):
    return _sdk(body.app_id).transcribe(
        body.media_path,
        model_size=body.model_size,
        device=body.device,
        compute_type=body.compute_type,
        language=body.language,
    )


@app.post("/v1/tts")
def tts(body: TTSBody):
    return _sdk(body.app_id).tts(
        body.text,
        output_wav=body.output_wav,
        piper_model=body.piper_model,
        kokoro_voice=body.kokoro_voice,
    )


@app.post("/v1/ocr")
def ocr(body: OCRBody):
    return _sdk(body.app_id).ocr(body.path)


@app.post("/v1/video")
def video(body: VideoBody):
    return _sdk(body.app_id).render_video(body.plan)


@app.post("/v1/vault/source")
def vault_source(body: VaultBytesBody):
    import base64
    return _sdk(body.app_id).vault_add_bytes(
        base64.b64decode(body.data_b64),
        original_name=body.original_name,
        mime_type=body.mime_type,
        metadata=body.metadata,
        role=body.role,
        locator=body.locator,
    )


@app.post("/v1/diagram")
def diagram(payload: dict):
    return {
        "backend": "Forge Core",
        "mode": "deterministic-manifest",
        "scene": payload,
        "cloud_used": False,
    }


@app.post("/v1/export")
def export(payload: dict):
    return {
        "backend": "Forge Core",
        "accepted": True,
        "export_manifest": payload,
        "cloud_used": False,
    }


@app.post("/v1/provenance")
def provenance(payload: dict):
    return {
        "backend": "Forge Core",
        "provenance": payload,
        "rule": "Every derived asset must reference its source_id or parent asset.",
    }


@app.post("/v1/ingest")
def ingest(body: IngestBody):
    import base64
    return _sdk(body.app_id).ingest_document_bytes(
        base64.b64decode(body.data_b64),
        original_name=body.original_name,
        mime_type=body.mime_type,
        metadata=body.metadata,
    )


@app.post("/v1/search")
def search(body: SearchBody):
    return {
        "backend": "Forge Core",
        "hits": _sdk(body.app_id).search(body.query, limit=body.limit),
    }
