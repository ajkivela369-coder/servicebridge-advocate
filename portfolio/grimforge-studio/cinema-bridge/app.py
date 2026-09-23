from __future__ import annotations

import asyncio
import json as pyjson
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
from typing import Any

import fal_client
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="GrimForge Cinema Bridge", version="0.3.0")
OUTPUT_DIR = Path(os.getenv("GRIMFORGE_OUTPUT_DIR", "./outputs")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

ENDPOINTS = {
    "wan22": os.getenv("WAN22_ENDPOINT", "").rstrip("/"),
    "ltx2": os.getenv("LTX2_ENDPOINT", "").rstrip("/"),
    "flux-schnell": os.getenv("FLUX_SCHNELL_ENDPOINT", "").rstrip("/"),
    "chatterbox": os.getenv("CHATTERBOX_ENDPOINT", "").rstrip("/"),
    "musetalk": os.getenv("MUSETALK_ENDPOINT", "").rstrip("/"),
    "realesrgan": os.getenv("REALESRGAN_ENDPOINT", "").rstrip("/"),
    "rife": os.getenv("RIFE_ENDPOINT", "").rstrip("/"),
}

FAL_ENABLED = bool(os.getenv("FAL_KEY"))

FAL_PROVIDER_LABELS = {
    "kling-v3": "Kling V3 Standard",
    "kling-o3-reference": "Kling O3 Reference",
    "kling-o3-4k": "Kling O3 Native 4K Reference",
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


class VoiceCreateRequest(BaseModel):
    voice_url: str


class AssembleRequest(BaseModel):
    clip_urls: list[str]
    width: int = 1280
    height: int = 720
    fps: int = 24
    title: str = "grimforge-episode"


def require_ffmpeg() -> tuple[str, str]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise HTTPException(
            status_code=503,
            detail="ffmpeg and ffprobe are required for full-episode assembly.",
        )
    return ffmpeg, ffprobe


def run_command(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-4000:] or "media command failed")


def has_audio_stream(ffprobe: str, file_path: Path) -> bool:
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "json",
            str(file_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return False
    try:
        data = pyjson.loads(completed.stdout or "{}")
        return bool(data.get("streams"))
    except Exception:
        return False


async def download_file(url: str, destination: Path) -> None:
    async with httpx.AsyncClient(timeout=60 * 30, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        destination.write_bytes(response.content)


async def assemble_clips(request: AssembleRequest, base_url: str) -> dict[str, Any]:
    ffmpeg, ffprobe = require_ffmpeg()
    clips = [url for url in request.clip_urls if url.startswith(("http://", "https://"))]
    if not clips:
        raise HTTPException(status_code=400, detail="At least one clip URL is required.")
    if len(clips) > 250:
        raise HTTPException(status_code=400, detail="Too many clips for one assembly job.")

    width = max(640, min(3840, request.width))
    height = max(360, min(2160, request.height))
    fps = max(12, min(60, request.fps))

    with tempfile.TemporaryDirectory(prefix="grimforge-assemble-") as tmp:
        tmpdir = Path(tmp)
        normalized: list[Path] = []

        for index, url in enumerate(clips):
            source = tmpdir / f"source-{index:04d}.mp4"
            target = tmpdir / f"normalized-{index:04d}.mp4"
            await download_file(url, source)
            audio = await asyncio.to_thread(has_audio_stream, ffprobe, source)

            video_filter = (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"fps={fps},format=yuv420p"
            )

            if audio:
                command = [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(source),
                    "-vf",
                    video_filter,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "18",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-movflags",
                    "+faststart",
                    str(target),
                ]
            else:
                command = [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(source),
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-vf",
                    video_filter,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "18",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    str(target),
                ]

            await asyncio.to_thread(run_command, command)
            normalized.append(target)

        concat_file = tmpdir / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in normalized),
            encoding="utf-8",
        )

        output_name = (
            "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in request.title)
            .strip("-")
            .lower()[:80]
            or "grimforge-episode"
        )
        output_name = f"{output_name}-{uuid.uuid4().hex[:8]}.mp4"
        output_path = OUTPUT_DIR / output_name

        await asyncio.to_thread(
            run_command,
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
        )

    public_base = os.getenv("GRIMFORGE_CINEMA_BRIDGE_PUBLIC_URL", "").rstrip("/")
    if public_base:
        url = f"{public_base}/outputs/{output_name}"
    else:
        url = f"{base_url.rstrip('/')}/outputs/{output_name}"

    return {
        "ok": True,
        "url": url,
        "clips": len(clips),
        "width": width,
        "height": height,
        "fps": fps,
    }


def clamp_duration(seconds: float | None) -> str:
    value = int(round(seconds or 5))
    return str(max(3, min(15, value)))


def extract_url(value: Any) -> str:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    if isinstance(value, dict):
        for key in (
            "url",
            "video_url",
            "videoUrl",
            "output_url",
            "outputUrl",
        ):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                return candidate
        # Prefer media-like fields before walking everything else.
        for key in ("video", "videos", "file", "output", "result", "data"):
            if key in value:
                candidate = extract_url(value[key])
                if candidate:
                    return candidate
        for candidate in value.values():
            found = extract_url(candidate)
            if found:
                return found
    if isinstance(value, list):
        for candidate in value:
            found = extract_url(candidate)
            if found:
                return found
    return ""


def kling_arguments(request: GenerateRequest) -> tuple[str, dict[str, Any]]:
    meta = request.metadata or {}
    duration = clamp_duration(request.seconds)
    voice_ids = meta.get("voice_ids") or ([request.voice_id] if request.voice_id else [])
    generate_audio = bool(meta.get("generate_audio", True))

    common: dict[str, Any] = {
        "prompt": request.prompt or "",
        "duration": duration,
        "generate_audio": generate_audio,
        "aspect_ratio": meta.get("aspect_ratio", "16:9"),
    }
    if request.negative_prompt:
        common["negative_prompt"] = request.negative_prompt
    if voice_ids:
        common["voice_ids"] = voice_ids[:2]
    if meta.get("multi_prompt"):
        common.pop("prompt", None)
        common["multi_prompt"] = meta["multi_prompt"]

    # Stable recurring characters / props / environments.
    if meta.get("image_urls"):
        common["image_urls"] = meta["image_urls"][:4]
    if meta.get("elements"):
        common["elements"] = meta["elements"]
    if meta.get("end_image_url"):
        common["end_image_url"] = meta["end_image_url"]

    if request.provider == "kling-v3":
        if request.image_url:
            common["start_image_url"] = request.image_url
            return "fal-ai/kling-video/v3/standard/image-to-video", common
        return "fal-ai/kling-video/v3/standard/text-to-video", common

    if request.provider == "kling-o3-reference":
        if not request.image_url:
            raise HTTPException(
                status_code=400,
                detail="kling-o3-reference requires a start/reference image for identity continuity.",
            )
        common["start_image_url"] = request.image_url
        common["shot_type"] = meta.get("shot_type", "customize")
        return "fal-ai/kling-video/o3/standard/reference-to-video", common

    if request.provider == "kling-o3-4k":
        if not request.image_url:
            raise HTTPException(
                status_code=400,
                detail="kling-o3-4k requires a start/reference image.",
            )
        common["start_image_url"] = request.image_url
        common["shot_type"] = meta.get("shot_type", "customize")
        return "fal-ai/kling-video/o3/4k/reference-to-video", common

    raise HTTPException(status_code=400, detail=f"Unsupported Kling provider: {request.provider}")


async def fal_subscribe(model_id: str, arguments: dict[str, Any]) -> Any:
    if not FAL_ENABLED:
        raise HTTPException(status_code=503, detail="FAL_KEY is not configured on the Cinema Bridge.")
    try:
        return await asyncio.to_thread(
            fal_client.subscribe,
            model_id,
            arguments=arguments,
            with_logs=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"fal/Kling generation failed: {exc}") from exc


@app.get("/health")
async def health() -> dict[str, Any]:
    configured = {k: bool(v) for k, v in ENDPOINTS.items()}
    configured.update({name: FAL_ENABLED for name in FAL_PROVIDER_LABELS})
    return {
        "ok": True,
        "configured": configured,
        "fal_enabled": FAL_ENABLED,
    }


@app.get("/v1/providers")
async def providers() -> dict[str, Any]:
    local = [
        {"id": name, "configured": bool(url), "kind": "self-hosted"}
        for name, url in ENDPOINTS.items()
    ]
    kling = [
        {
            "id": provider_id,
            "name": label,
            "configured": FAL_ENABLED,
            "kind": "fal-kling",
        }
        for provider_id, label in FAL_PROVIDER_LABELS.items()
    ]
    return {"providers": local + kling}


async def forward_local(request: GenerateRequest) -> Any:
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


async def generate_kling(request: GenerateRequest) -> dict[str, Any]:
    model_id, arguments = kling_arguments(request)
    result = await fal_subscribe(model_id, arguments)
    url = extract_url(result)
    if not url:
        raise HTTPException(
            status_code=502,
            detail="Kling completed but the bridge could not find a playable output URL.",
        )
    return {
        "ok": True,
        "provider": request.provider,
        "model_id": model_id,
        "url": url,
        "result": result,
    }


@app.post("/v1/assemble")
async def assemble(request: AssembleRequest, http_request: Request) -> Any:
    return await assemble_clips(request, str(http_request.base_url))


@app.post("/v1/video/generate")
async def video(request: GenerateRequest) -> Any:
    if request.provider.startswith("kling-"):
        return await generate_kling(request)
    return await forward_local(request)


@app.post("/v1/kling/voice/create")
async def create_kling_voice(request: VoiceCreateRequest) -> Any:
    result = await fal_subscribe(
        "fal-ai/kling-video/create-voice",
        {"voice_url": request.voice_url},
    )
    voice_id = result.get("voice_id") if isinstance(result, dict) else None
    if not voice_id:
        raise HTTPException(status_code=502, detail="Kling returned no voice_id.")
    return {"voice_id": voice_id}


@app.post("/v1/image/generate")
async def image(request: GenerateRequest) -> Any:
    return await forward_local(request)


@app.post("/v1/voice/generate")
async def voice(request: GenerateRequest) -> Any:
    return await forward_local(request)


@app.post("/v1/dialogue-video/generate")
async def dialogue_video(request: GenerateRequest) -> Any:
    return await forward_local(request)


@app.post("/v1/upscale")
async def upscale(request: GenerateRequest) -> Any:
    return await forward_local(request)


@app.post("/v1/interpolate")
async def interpolate(request: GenerateRequest) -> Any:
    return await forward_local(request)
