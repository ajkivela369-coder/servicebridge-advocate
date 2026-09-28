# Forge v0.5.6 — Workflow Recovery + Defense PDF Restoration candidate

This build advances the v0.5.4 Media/3D candidate without discarding its Core, Vault, Blender, ComfyUI, FFmpeg, packet, or Windows installer work.

## What changed

- Six-product premium design system: blue Workspace, emerald Elias, violet Evidence Auditor, crimson MedForge, orange/gold GrimForge, blue-book Forge Learn.
- Workspace and Learn are fully separate but synchronized.
- Elias remains a standalone conversational/document assistant; Evidence Auditor context is optional.
- Evidence Auditor has multi-file batch intake and a prominent Upload Evidence → Build Packet fast lane for VBA, SSDI, APTD, ADA, Clinician, or Custom PDF packets.
- GrimForge Simple mode now exposes one-click Generate Full Episode plus explicit **3D / 2.5D / 2D** animation style selection.
- 3D uses Blender; 2.5D uses generated images plus cinematic depth-style camera motion; 2D uses the configured ComfyUI video workflow.
- MedForge keeps local image analysis, generated visuals and shared Blender 3D mechanism rendering.
- App-specific Copilots now expose real workflow actions in addition to chat.
- One Desktop **Forge Apps** folder contains unique app shortcuts; older loose Forge shortcuts are cleaned up.
- Approved design reference images are included in `DESIGN_REFERENCE/` and treated as visual acceptance targets.

## Install / upgrade

1. Extract this ZIP into a fresh temporary folder.
2. Double-click `INSTALL_FORGE.cmd`.
3. Leave **Install shared Media / 3D Tools (Blender + FFmpeg)** checked if you want MedForge 3D and GrimForge 3D animation.
4. Click **INSTALL FORGE + LOCAL APPS**.

The installer is designed to preserve your Forge Home, Vault, user settings and outputs while replacing the current runtime. It stops the old Core first to avoid the Windows file-lock problem found in v0.5.0.

## Acceptance boundary

Static UI, Python/JavaScript syntax, learning synchronization, evidence packet fixture workflows and media assembly fixtures are tested in the build environment. Real Windows upgrade behavior, real Blender visual output, real ComfyUI image/video quality, real local model quality and narrator voice quality must still be tested on the target PC before calling v0.5.6 a final release.


## v0.5.6 workflow recovery

This pass responds to live Windows regression testing. GrimForge now preflights visual engines and can use explicit installed fallbacks instead of hard-stopping when optional ComfyUI imagery is not configured. MedForge again has a single end-to-end teaching-package action rather than disconnected utility panels. Evidence Auditor's PDF generator now builds a defense-style, source-controlled front section and appends the original exhibits intact.
