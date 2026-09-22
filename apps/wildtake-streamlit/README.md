# WildTake Studio

Standalone Streamlit prototype for producing original narrated animal/wildlife short-form videos.

## Streamlit Community Cloud
Use this entry point:

apps/wildtake-streamlit/app.py

## Current features
- Simple / Pro modes
- video upload and preview
- mandatory Rights Preflight
- original narrator presets
- manual timestamped action beats
- editable commentary script
- 9:16 output target
- separate audio-lane planning
- provider status and honest not-connected states
- render/QC controls and production queue

The Aussie Wildlife Commentator is an original broad-style preset. It must not imitate or reproduce Ozzy Man Reviews / Ethan Marrell's voice, identity, scripts, catchphrases, or branding.

No API secrets are committed to this repository.

## Live deployment

https://wildtake-studio-i0atj8.v2.appdeploy.ai/

The Streamlit prototype remains the lightweight test bench. The public AppDeploy build is the current browser-facing WildTake experience.

## Shared video core

Future vision, TTS, captions, mixing, continuity, render, and QC adapters should use the provider-neutral contracts under `apps/video-core/` so WildTake and GrimForge Cinema share one production model.
