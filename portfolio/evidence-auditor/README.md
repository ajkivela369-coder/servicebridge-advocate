# Elias Evidence Auditor Pro

**Current production build:** https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

**Start here:** [`00_CURRENT_APP/`](./00_CURRENT_APP/)

This directory has been cleaned up so the current Elias application is the obvious entry point. The previous Streamlit implementation is preserved under [`legacy-streamlit/`](./legacy-streamlit/) rather than competing with the current build at the top level.

## What the current app does

Elias is a private, source-grounded evidence workspace for complex VA, disability, medical, service, and administrative records. The current production build combines fast AI assistance with deliberate manual review controls instead of forcing the user into a single chat-only workflow.

Key capabilities include:

- large searchable PDF indexing with visible upload, reading, and indexing states
- OCR intake for screenshots and scanned document images
- image, audio, and sampled-video-frame analysis
- persistent case memory and multiple chat threads
- floating **Elias Copilot** available throughout the workspace
- one-click **Strongest Evidence**, **Missing Evidence**, **Contradiction Check**, **Build Timeline**, **C&P Rebuttal**, and **Packet QA** passes
- manual evidence tools and plugins that remain independently selectable
- Case Review with source inventory, evidence gaps, tensions, chronology, and strongest-evidence analysis
- VA Law & Rater Lens with official-reference links and clear separation between governing criteria and case evidence
- public URL / YouTube research with explicit provenance boundaries
- optional live web search and neural voice when configured
- browser/device voice fallback and voice presets
- Packet Studio with one-click preflight plus full manual packet drafting
- visible full-screen working states that prevent repeated clicks from launching duplicate jobs

## Fastest way to evaluate it

1. Open the **current production build** above.
2. Sign in.
3. Add a searchable PDF or image.
4. Wait for the file card to show **Ready**.
5. Open the floating **Elias Copilot** and run **Strongest Evidence** or **Contradiction Check**.
6. Open **Case Review** to inspect the structured evidence and law tools.
7. Open **Packet Studio**, run **One-click preflight**, then generate a draft.

## Current vs. legacy

| Path | Status | Purpose |
|---|---|---|
| [`00_CURRENT_APP/`](./00_CURRENT_APP/) | **Current** | Production Elias AppDeploy build, live test link, feature map, and evaluation path |
| [`legacy-streamlit/`](./legacy-streamlit/) | Legacy | Prior Streamlit implementation preserved for regression/reference work |

The AppDeploy deployment is the source of truth for the current production application. The legacy Streamlit code remains useful as an open reference implementation, but it should not be mistaken for the newest build.

## Privacy boundary

The public repository contains only public-safe code and fictional/de-identified examples. Do **not** commit real VA records, medical records, service records, claim numbers, private case indexes, or personally identifying screenshots.

Elias helps a human reviewer find, organize, compare, and draft from evidence. It does not independently determine service connection, diagnostic validity, disability percentage, legal sufficiency, or entitlement to benefits.
