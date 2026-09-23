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


## Kling provider

To enable Kling V3 / O3 / O3 native-4K routes through fal:

```bash
export FAL_KEY=your_server_side_fal_key
```

Keep this key on the Cinema Bridge server. Do not place it in the browser or React bundle.

Available normalized provider IDs:

- `kling-v3` — standard V3 text/image-to-video route
- `kling-o3-reference` — O3 reference-guided cinematic route
- `kling-o3-4k` — O3 native-4K reference route

GrimForge uses signed temporary reference-frame URLs for reference-guided Kling rendering.

## Full episode assembly

Install `ffmpeg` and `ffprobe` on the Cinema Bridge host. The bridge normalizes the selected Golden Takes to one resolution/frame rate/audio layout and concatenates them into a single MP4.

Optionally set:

```bash
export GRIMFORGE_CINEMA_BRIDGE_PUBLIC_URL=https://cinema.example.com
export GRIMFORGE_OUTPUT_DIR=/var/lib/grimforge/outputs
```

The browser needs to be able to reach the public output URL returned by the bridge.

## Cinematic Photoreal 3D · 4K target

This preset is intended to read like a photographed prestige fantasy feature rather than glossy game CGI:

- natural skin, eyes, hair and facial hair
- aged steel, leather, wool, dirt, scratches and moisture
- practical torch/firelight plus cool ambient light
- shallow depth of field and plausible lens behavior
- grounded medieval production design
- restrained desaturated blue/amber grade
- realistic body weight and physics
- character/set bibles for cross-shot continuity

4K is a delivery/finishing resolution; the film look comes from the full reference + cinematography + lighting + continuity + take-selection pipeline.
