# GrimForge War Theater

**Authoritative build:** GitHub + Streamlit.

## Streamlit Community Cloud

Deploy with:

- Repository: `ajkivela369-coder/servicebridge-advocate`
- Branch: `main`
- Main file path: `apps/grimforge-war-theater/app.py`

Suggested public slug: `grimforge-war-theater`

## Current test reference

https://youtu.be/XQ1jlW7hQrA?si=uSU_l2gwdhQopib4

The YouTube reference is used only for broad production mechanics such as pacing, scale, shot rhythm, camera grammar, narration density, lighting, sound structure, and story rhythm. The app does not copy source characters, lore, dialogue, scripts, music, branding, or visual assets.

## What works now

- Simple / Pro modes
- preset-first Simple workflow
- Surprise Me preset randomization
- original faction presets
- editable Reference Lens presets
- deterministic original episode generation
- playable in-browser animatic with scene timeline, autoplay, play/pause, previous/next, progress, narration/dialogue, camera/sound/continuity notes
- **Source-Locked Visuals**: use a public image URL or uploaded PNG/JPG/WebP as a pixel-stable truth layer for maps, diagrams, scans, evidence photos, and educational explainers
- scene-level source framing controls (focus X/Y + zoom) so Forge can pan/zoom without redrawing the source
- portable project export embeds uploaded source images and records source/rights metadata
- full Pro filmmaking workspace
- continuity locks
- audio lane planning and loudness target
- takes / Keep / Maybe / Reject / Golden Fragment controls
- rights and export intent
- Director Veyr local copilot advice
- provider-aware final render queue
- explicit distinction between **Playable Animatic** and **Final Full-Motion Render**

## Provider status

The Streamlit build does **not** pretend that unconnected services are available.

Currently local:
- preset / project logic
- episode generator
- source-locked media import / project persistence
- source-locked pan/zoom animatic player
- animatic player
- Veyr deterministic advice
- QC / render planning

Still provider-dependent:
- automated reference-video analysis
- full-motion AI video generation
- premium TTS / performance voices
- generated music and SFX
- cloud final MP4 rendering

Those should plug into the provider-neutral shared contracts under `apps/video-core/`.

## Local run

```bash
cd apps/grimforge-war-theater
python -m pip install -r requirements.txt
streamlit run app.py
```

## Tests

The deterministic engine is covered by `tests/test_grimforge_war_engine.py` and is included in repository CI.

## Older deployments

The earlier AppDeploy version remains useful as an experimental backend branch:

https://grimforge-war-theater-0s8pee.v2.appdeploy.ai/

The unfinished Lovable remix is no longer the authoritative build while workspace credits are unavailable.


## Railway deployment

Production service:
- Root directory: `apps/grimforge-war-theater`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
- Live deployment: https://grimforge-war-theater-production.up.railway.app

## Portable projects and render manifests

GrimForge project state can be exported as JSON and imported again later. A forged episode can also export a provider-neutral render manifest. The manifest intentionally uses the stage `planned` until a real video worker returns generated media; a plan or animatic must never be labeled as a final render.

The app also shows heuristic routing guidance for the selected open video model and free GPU backend. That guidance is not live VRAM detection and does not imply a provider is connected.


## Source-Locked Visuals

Use **Reference Theater → Source-Locked Visuals** when the visual must remain faithful to a real source rather than be regenerated.

Supported sources:
- a direct public image URL
- an uploaded PNG, JPG/JPEG, or WebP

When **Lock source geometry** is enabled, GrimForge treats the image as the truth layer. The animatic may crop, pan, zoom, dim, and place text/graphics above it, but the source pixels are not generatively redrawn.

In Pro mode, each scene exposes **Focus X**, **Focus Y**, and **Zoom** controls. This is designed for map walkthroughs, medical/technical diagrams, evidence images, satellite/aerial screenshots, and other explanatory content where spatial accuracy matters.

Uploaded sources are embedded as data URIs in the exported project JSON for portability. Public URLs are preserved as URLs. Always record an appropriate rights/source note for material you did not create.
