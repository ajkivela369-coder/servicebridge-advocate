# Forge Suite — Current Source

**Synced version:** v0.5.6 — Workflow Recovery + Defense PDF Restoration candidate

This folder is the canonical GitHub mirror of the current local Forge Suite source.

## Product map

| Product | Current role |
|---|---|
| Forge Workspace | Local system control center, models, health, backups, shared dependencies, media/3D tools and app launch |
| Elias | Standalone conversational/document assistant with local model routing |
| Evidence Auditor | Evidence ingestion, provenance, review/chronology and defense-style PDF packet workflows |
| MedForge | Medical image/mechanism teaching, visual generation and Blender-backed 3D studio paths |
| GrimForge | Full-episode 3D / 2.5D / 2D production with narration, captions and MP4 assembly |
| Forge Learn | Parallel teaching app synchronized to shipping Forge capabilities |

## Architecture

All six surfaces use **Forge Core** for shared model routing, local storage/Vault services, evidence workflows, learning synchronization, media generation, FFmpeg assembly, Blender integration, hardware-aware fallbacks and recovery.

Blender and FFmpeg are shared dependencies, not per-app copies. ComfyUI is an optional local image/video layer.

## Build + upgrade history

See [BUILD_AND_UPGRADE.md](current/BUILD_AND_UPGRADE.md) for the step-by-step evolution of the six-product Forge architecture and the current acceptance sequence.

## Acceptance boundary

This source is an **implementation candidate**, not a claim that every optional engine is production-validated on every PC.

Still requiring target-PC acceptance:

1. Windows in-place upgrade while preserving Forge Home, Vault, settings and outputs.
2. Real Blender MedForge and GrimForge render quality.
3. Real ComfyUI image/video generation with installed workflows/models.
4. Real local British narrator quality.
5. Visual comparison against approved product references at normal laptop scaling.

Read [current acceptance status](current/ACCEPTANCE_STATUS.md), [read-me-first](current/READ_ME_FIRST.md), and [product blueprint](current/PRODUCT_COMPLETION_BLUEPRINT.md).

## Source-control boundary

Do **not** commit private Vault contents, claimant/case records, secrets, downloaded model weights, local caches, or generated evidence packets containing personal information. This mirror contains code, configuration, synthetic fixtures and product assets only.