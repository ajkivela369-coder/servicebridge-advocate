from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="GrimForge Cinema Bridge", version="0.1.0")

ENDPOINTS = {
    "wan22": os.getenv("WAN22_ENDPOINT", "").rstrip("/"),
    "ltx2": os.getenv("LTX2_ENDPOINT", "").rstrip("/"),
    "flux-schnell": os.getenv("FLUX_SCHNELL_ENDPOINT", "").rstrip("/"),
    "chatterbox": os.getenv("CHATTERBOX_ENDPOINT", "").rstrip("/"),
    "musetalk": os.getenv("MUSETALK_ENDPOINT", "").rstrip("/"),
    "realesrgan": os.getenv("REALESRGAN_ENDPOINT", "").rstrip("/"),
    "rife": os.getenv("RIFE_ENDPOINT", "").rstrip("/"),
}

class GenerateRequest(BaseModel):
    provider: str
    prompt: str | None = None
    negative_prompt: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    width: int | None = None
    height: int | None = None
    fps: int | None = None
    seconds: float | None = None
    seed: int | None = None
    voice_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "configured": {k: bool(v) for k, v in ENDPOINTS.items()}}

@app.get("/v1/providers")
async def providers() -> dict[str, Any]:
    return {
        "providers": [
            {"id": name, "configured": bool(url)}
            for name, url in ENDPOINTS.items()
        ]
    }

async def forward(kind: str, request: GenerateRequest) -> Any:
    endpoint = ENDPOINTS.get(request.provider, "")
    if not endpoint:
        raise HTTPException(
            status_code=503,
            detail=f"{request.provider} is not configured on this Cinema Bridge",
        )

    payload = request.model_dump(exclude_none=True)

    async with httpx.AsyncClient(timeout=60 * 60) as client:
        response = await client.post(f"{endpoint}/generate", json=payload)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text[:2000],
        )

    try:
        return response.json()
    except Exception:
        return {"ok": True, "raw": response.text}

@app.post("/v1/video/generate")
async def video(request: GenerateRequest) -> Any:
    return await forward("video", request)

@app.post("/v1/image/generate")
async def image(request: GenerateRequest) -> Any:
    return await forward("image", request)

@app.post("/v1/voice/generate")
async def voice(request: GenerateRequest) -> Any:
    return await forward("voice", request)

@app.post("/v1/dialogue-video/generate")
async def dialogue_video(request: GenerateRequest) -> Any:
    return await forward("dialogue-video", request)

@app.post("/v1/upscale")
async def upscale(request: GenerateRequest) -> Any:
    return await forward("upscale", request)

@app.post("/v1/interpolate")
async def interpolate(request: GenerateRequest) -> Any:
    return await forward("interpolate", request)
