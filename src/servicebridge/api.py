from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    raise RuntimeError("API support requires: pip install 'servicebridge-advocate[api]'") from exc

from forge_core.adapters import ForgeEmbeddingProvider, ForgeTextProvider
from forge_core.sdk import ForgeSDK

from .advocate import Advocate
from .models import AdvocacyMode, AdvocacyRequest, BenefitLane
from .local_runtime import RuntimeMode
from .local_runtime.evidence import LocalSemanticEvidenceStore
from .local_runtime.memory import LocalVectorStore
from .store import EvidenceStore


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=10_000)
    lane: BenefitLane = BenefitLane.GENERAL
    mode: AdvocacyMode = AdvocacyMode.PRIVATE_ANALYSIS
    audience: str = Field(default="claimant", max_length=200)
    requested_output: str = Field(default="analysis", max_length=200)
    top_k: int = Field(default=8, ge=1, le=30)
    runtime_mode: RuntimeMode = RuntimeMode.CREDITLESS
    use_openai: bool = False  # legacy flag; requires explicit cloud mode/admin opt-in


app = FastAPI(
    title="ServiceBridge Advocate",
    version="0.1.0",
    description="Evidence-grounded advocacy API. Not medical or legal advice.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ask")
def ask(body: AskBody) -> dict[str, object]:
    if body.runtime_mode == RuntimeMode.CLOUD or body.use_openai:
        raise HTTPException(
            status_code=400,
            detail=(
                "Elias no longer selects cloud/model providers directly. "
                "Set Forge Core to Hybrid mode instead."
            ),
        )

    forge = ForgeSDK.for_app("elias")
    provider = ForgeTextProvider(forge)

    database = os.getenv("SERVICEBRIDGE_DB", "./private_data/servicebridge.sqlite3")
    request = AdvocacyRequest(
        question=body.question,
        lane=body.lane,
        mode=body.mode,
        audience=body.audience,
        requested_output=body.requested_output,
        top_k=body.top_k,
    )

    with EvidenceStore(database) as store:
        if os.getenv("SERVICEBRIDGE_USE_LOCAL_SEMANTIC") == "1":
            vector_db = os.getenv(
                "SERVICEBRIDGE_VECTOR_DB",
                "./private_data/local_runtime/evidence_vectors.sqlite3",
            )
            embedder = ForgeEmbeddingProvider(forge)
            with LocalVectorStore(vector_db) as vectors:
                retriever = LocalSemanticEvidenceStore(store, vectors, embedder)
                response = Advocate(retriever, provider).answer(request)
        else:
            response = Advocate(store, provider).answer(request)
    return response.to_dict()
