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


## Added autonomy layers

### Local semantic memory
- llama.cpp-compatible local embedding client
- SQLite vector store with cosine scoring
- hybrid evidence retrieval that fuses local full-text and semantic ranks
- one-command local semantic evidence indexing

### Local documents
- pypdf embedded-text extraction
- opt-in PaddleOCR for scans and image-only evidence
- OCR results pass through the normal ServiceBridge redaction, chunking, provenance, and evidence-store pipeline

### Offline model catalog
Model files are registered explicitly with local paths, optional hashes, minimum RAM/VRAM, and quality rank. Creditless Mode never downloads missing model weights automatically.

### Direct local image generation
A Diffusers worker can load a model from an existing local directory with `local_files_only=True`. ComfyUI remains an optional workflow engine rather than a required UI/server.

### Deterministic local media
The runtime can:
- create scene videos from still images
- add local narration or generated silence
- normalize audio loudness
- mix/duck local music beneath narration
- generate SRT captions directly from known scene narration
- concatenate scenes
- burn captions
- render a final H.264/AAC MP4

### Local workflow registry
Saved JSON workflows can be registered, verified, hashed, and parameterized locally. This is intended for optional ComfyUI image/video workflows.

### Localhost gateway
`scripts/local_runtime_server.py` exposes loopback-only status, local text generation, and local embeddings. It does not expose a cloud fallback in Creditless Mode.

## App integration

The current branch adds Runtime Mode to:
- GrimForge War Theater
- MedForge Imaging Studio
- WildTake Studio
- ServiceBridge/Elias API

Creditless is the default runtime mode.

## Teaching surface

`apps/forge-systems-lab/` is the parallel learning/control app. It reads the real local-runtime modules and teaches the same code paths used by the apps.
