# VocalForge — Build + Upgrade History

VocalForge is a local-first vocal recording, analysis, enhancement, comparison, and export workstation. This history records what has actually been implemented or documented and keeps later-phase ideas separate from current MVP evidence.

## 1. Product need

The project began with a practical goal: make short, comfortable vocal takes easier to capture, analyze, improve, compare, and export without requiring a singer to force more physical effort.

The design therefore starts with preserved source recordings and an inspectable processing chain rather than destructive editing.

## 2. MVP architecture

The current MVP specification uses a local/open stack:

- FFmpeg for conversion and rendering.
- Spotify Pedalboard for DSP and optional VST3 hosting.
- librosa / NumPy / SciPy for analysis.
- soundfile for audio I/O.
- DeepFilterNet as an optional local noise-removal route.
- Forge file-vault conventions for preserving originals and derived outputs.

Commercial tools such as Melodyne or iZotope Nectar are optional, user-authorized integrations when compatible plugins are already installed. They are not bundled or silently loaded.

## 3. Primary workflow

Record → Analyze → Clean → Stabilize → Tune → Polish → Compare → Export

The product separates three working modes:

- **Natural / Pure** — conservative cleanup and stabilization.
- **Studio Vocal** — a more produced chain with dynamics, tuning, ambience, and mastering controls.
- **Comfort Mode** — short-take workflow, preserved takes, comparison, and assisted production without prompts to force vocal effort.

## 4. Implementation progression

### Product specification

Defined the source-preservation rule, processing stages, analysis metrics, export formats, optional plugin boundary, and MVP acceptance criteria.

### Local audio API

Added a local audio API so the workstation can perform its core processing without requiring a mandatory cloud service.

### Interactive workstation

Added controls for capture/import, analysis, processing, comparison, and export.

### Working MVP documentation — 2026-10-03

The Forge source repository records the current working MVP and technical specification. Later features such as phrase-level comping, real-time low-latency monitoring, harmony generation, formant-safe tuning, stem separation, mobile remote control, and deeper Workspace integration remain future phases unless separately verified.

## 5. Verification boundary

A working MVP does not mean every planned audio feature is finished. Current claims should be limited to the implemented/documented local workflow and any functions that pass real audio tests.

Recommended acceptance run:

1. Record or import a short WAV.
2. Confirm the original remains untouched.
3. Generate waveform/pitch and basic performance metrics.
4. Run Natural / Pure processing.
5. A/B the original and processed render.
6. Export a WAV.
7. Record the exact processing chain and any optional plugin used.

## 6. Source of truth

Current technical specification: [Forge AI Suite — VOCALFORGE_MVP.md](https://github.com/ajkivela369-coder/forge-ai-suite/blob/main/docs/VOCALFORGE_MVP.md)

Forge Learn v0.5.9 contains the synchronized teaching entry for this workflow.
