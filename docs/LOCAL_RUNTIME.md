# ServiceBridge / Forge Local Runtime

The Local Runtime is the shared execution layer for Elias/ServiceBridge, GrimForge, MedForge, WildTake, and future Build Labs.

## Goal

Every core workflow should have a **Creditless Mode** that remains useful when paid APIs are disconnected.

Creditless Mode means:
- local endpoints only
- no automatic cloud fallback
- content-addressed caching
- explicit capability degradation
- deterministic local rendering where generative models are unavailable

## Current core

- runtime policy with hard local-network enforcement
- hardware profiling
- local service discovery
- llama.cpp/OpenAI-compatible local text client
- SQLite job queue
- content-addressed asset vault
- FFmpeg command builders
- faster-whisper adapter
- Piper TTS adapter
- ComfyUI local API adapter
- runtime doctor CLI

## Recommended local topology

```
Apps
  ├─ Elias / ServiceBridge
  ├─ GrimForge
  ├─ MedForge
  ├─ WildTake
  └─ Build Labs
        │
        ▼
ServiceBridge Local Runtime
  ├─ llama.cpp        text / VLM / embeddings later
  ├─ faster-whisper   speech to text
  ├─ Piper            text to speech
  ├─ ComfyUI          image / optional local video
  ├─ FFmpeg           deterministic rendering
  ├─ TotalSegmentator medical segmentation worker
  ├─ SQLite           jobs / evidence / cache metadata
  └─ Asset Vault      reusable source + derived assets
```

## Doctor

```bash
python scripts/local_runtime_doctor.py
```

The doctor never treats a missing local engine as a reason to call a paid API.

## Offline-model note

Open-source tools may download model weights the first time they are installed or run. For a truly offline environment, download the required models in advance and store them under the local model directory.

## Security boundary

Creditless Mode permits only localhost/loopback HTTP endpoints. External network access requires switching modes and an explicit allow policy.

## Planned next layers

1. local embedding + vector index
2. OCR/document worker
3. shared local model catalog
4. deterministic caption/audio/video renderer
5. Blender scene/export bridge
6. local image workflows
7. optional local video generation when hardware allows
