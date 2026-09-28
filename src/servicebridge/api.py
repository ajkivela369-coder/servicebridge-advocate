from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    raise RuntimeError("API support requires: pip install 'servicebridge-advocate[api]'") from exc

from .advocate import Advocate
from .models import AdvocacyMode, AdvocacyRequest, BenefitLane
from .local_runtime import RuntimeMode
from .providers import provider_for_runtime
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
    runtime_mode = body.runtime_mode
    if body.use_openai and runtime_mode != RuntimeMode.CLOUD:
        raise HTTPException(
            status_code=400,
            detail="Legacy use_openai=true now requires runtime_mode='cloud'.",
        )

    if runtime_mode == RuntimeMode.CLOUD:
        if os.getenv("SERVICEBRIDGE_ALLOW_CLOUD") != "1":
            raise HTTPException(
                status_code=403,
                detail="Cloud runtime is disabled. Set SERVICEBRIDGE_ALLOW_CLOUD=1 to opt in.",
            )
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
        provider = provider_for_runtime(
            mode=RuntimeMode.CLOUD,
            cloud_model=os.getenv("SERVICEBRIDGE_MODEL"),
            allow_external_network=True,
            allow_cloud_fallback=True,
        )
    else:
        provider = provider_for_runtime(
            mode=runtime_mode,
            local_endpoint=os.getenv(
                "SERVICEBRIDGE_LOCAL_LLM_ENDPOINT",
                "http://127.0.0.1:8080/v1/chat/completions",
            ),
            local_model=os.getenv("SERVICEBRIDGE_LOCAL_MODEL", "local-model"),
            allow_external_network=False,
            allow_cloud_fallback=False,
        )

    database = os.getenv("SERVICEBRIDGE_DB", "./private_data/servicebridge.sqlite3")
    with EvidenceStore(database) as store:
        response = Advocate(store, provider).answer(
            AdvocacyRequest(
                question=body.question,
                lane=body.lane,
                mode=body.mode,
                audience=body.audience,
                requested_output=body.requested_output,
                top_k=body.top_k,
            )
        )
    return response.to_dict()
