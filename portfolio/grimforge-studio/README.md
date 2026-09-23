# GrimForge Studio — Reference Lab release source

This folder preserves the existing Streamlit GrimForge prototype and now also contains an `appdeploy/` source tree for the newer cinematic web studio.

## Simple vs Pro workflow

### Simple mode — default
Simple mode is the creator-first front door:

1. Paste a public YouTube video/channel or website.
2. Tell Archivist Veyr what original episode you want.
3. Choose only the world and approximate runtime.
4. Click **Veyr — Make the Full Cinematic Episode**.

Veyr then handles the pre-render production pipeline: accessible-reference analysis, original episode structure, full narration, separate scene dialogue, cinematography, camera movement, sound direction, claim/source labels, YouTube title/thumbnail packaging, and automatic generated scene art. The completed package drops directly into the episode/animatic preview.

If a YouTube page does not expose transcript/content text publicly, GrimForge does not claim Veyr watched or transcribed it.

### Pro mode
Pro retains the technical studio: YouTube Mixer, imported Reference Lab profiles and weights, cinematography direction, scene-level narration/dialogue editing, art generation, Kokoro/browser voice controls, speech profiles, source/canon auditing, rights controls, production-readiness status, render handoff, cloud save and publishing tools.

Simple → Pro preserves the current episode and generated scene work.

## Reference Lab upgrade
- Existing curated YouTube Mixer stays intact.
- Paste a public YouTube channel/video or website into **Reference Lab**.
- Veyr creates a reusable six-axis production profile: Depth, Humor, Motion, Pace, Hook, Beginner clarity.
- Imported references become weighted members of the same production mixer as the built-in channel presets.
- Reference profiles can be reweighted or removed.
- The combined blend influences episode generation/remixing and is saved with the cloud project.
- Floating **Archivist Veyr** remains available throughout the studio.

## Originality boundary
Imported channels and sites influence abstract production traits only. GrimForge explicitly avoids copying scripts, jokes, catchphrases, thumbnails, artwork, creator identity, voices, or distinctive protected expression.

## Live version
Current deployed version:
https://grimforge-studio-xtkoo5.v2.appdeploy.ai/

The GitHub `appdeploy/` source is ahead of the live deployment because the AppDeploy daily free-tier deployment budget was exhausted during the upgrade session.
