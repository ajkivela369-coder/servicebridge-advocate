# Creditless Setup

The objective is **no recurring paid-provider dependency for core workflows**.

Open-source packages and local model files are still dependencies; the difference is that they run on hardware you control and do not consume per-call credits.

## One-time setup

### Windows

From PowerShell in the repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_creditless_windows.ps1
```

Optional local transcription and OCR Python packages:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_creditless_windows.ps1 -WithWhisper -WithOCR
```

### macOS / Linux

```bash
bash scripts/bootstrap_creditless_unix.sh
```

## Local engine roles

- **llama.cpp**: local text/VLM/embedding/reranking server
- **FFmpeg**: deterministic video/audio/caption renderer
- **faster-whisper**: local transcription
- **Piper**: local narration
- **PaddleOCR**: local OCR/document recognition
- **ComfyUI**: optional local image/video workflow engine
- **TotalSegmentator**: optional medical segmentation worker
- **SQLite**: evidence DB, semantic vectors, cache metadata, and job queue

None of these should trigger a cloud fallback in Creditless Mode.

## Model provisioning

Creditless Mode intentionally does not download model weights implicitly.

1. Download/provision an appropriate model once.
2. Put it in a private model directory.
3. Register the file:

```bash
python scripts/local_model_catalog.py add \
  --id local-text-small \
  --kind text \
  --path private_data/local_runtime/models/model.gguf \
  --format gguf \
  --min-ram-gb 8 \
  --quality-rank 1 \
  --hash
```

4. Verify:

```bash
python scripts/local_model_catalog.py verify --id local-text-small
```

## Local runtime

Inspect the machine:

```bash
python scripts/local_runtime_doctor.py
```

Run the localhost gateway:

```bash
python scripts/local_runtime_server.py
```

The default gateway binds only to `127.0.0.1` and uses Creditless Mode.

## Elias semantic evidence search

Start a local embedding-capable llama.cpp server, then index evidence:

```bash
python scripts/local_semantic_index.py
```

To let the ServiceBridge API use that index:

```
SERVICEBRIDGE_USE_LOCAL_SEMANTIC=1
```

Full-text SQLite search remains available when embeddings are absent.

## Offline preparation checklist

Before disconnecting a machine from the internet, confirm:
- required model weights are present
- hashes verify
- local voices are installed
- OCR/transcription models have been cached
- FFmpeg is available
- the runtime doctor shows the expected engines
- representative jobs have been tested while offline

The apps should degrade to manual/deterministic local workflows when an optional model is missing.
