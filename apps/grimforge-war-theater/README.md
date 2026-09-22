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
