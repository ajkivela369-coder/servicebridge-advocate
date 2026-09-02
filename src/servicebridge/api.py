from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    raise RuntimeError("API support requires: pip install 'servicebridge-advocate[api]'") from exc

from .advocate import Advocate
from .models import AdvocacyMode, AdvocacyRequest, BenefitLane
from .providers import OpenAIProvider, PromptOnlyProvider
from .store import EvidenceStore


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=10_000)
    lane: BenefitLane = BenefitLane.GENERAL
    mode: AdvocacyMode = AdvocacyMode.PRIVATE_ANALYSIS
    audience: str = Field(default="claimant", max_length=200)
    requested_output: str = Field(default="analysis", max_length=200)
    top_k: int = Field(default=8, ge=1, le=30)
    use_openai: bool = False


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
    if body.use_openai and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
    provider = OpenAIProvider() if body.use_openai else PromptOnlyProvider()
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
