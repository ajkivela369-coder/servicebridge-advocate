# GrimForge Cinema Bridge

A thin normalization layer between GrimForge's website and self-hosted GPU generation engines.

The bridge intentionally does not bundle model weights. Install the official repositories you choose, then expose their inference through local/provider-specific adapters.

## Recommended providers

- Wan2.2 — default permissive cinematic video engine
- LTX-2.x — optional Cinematic Max audio/video engine
- FLUX.1-schnell — hero frames / character sheets
- Chatterbox — narration / character voices
- MuseTalk — dialogue lip-sync
- Real-ESRGAN — upscale / restoration
- RIFE — interpolation / motion smoothing

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7869
```

Configure endpoints for whichever model servers you have running:

```bash
WAN22_ENDPOINT=http://localhost:8188/wan
LTX2_ENDPOINT=http://localhost:8188/ltx
FLUX_SCHNELL_ENDPOINT=http://localhost:8188/flux
CHATTERBOX_ENDPOINT=http://localhost:4123
MUSETALK_ENDPOINT=http://localhost:8001
REALESRGAN_ENDPOINT=http://localhost:8002
RIFE_ENDPOINT=http://localhost:8003
```

GrimForge then points to this bridge with `GRIMFORGE_CINEMA_BRIDGE_URL`.
