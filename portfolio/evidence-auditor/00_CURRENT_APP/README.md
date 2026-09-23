# Elias + Evidence Auditor — Unified Flagship App

> **Start here.** This folder points to the current production build. The older Streamlit implementation lives under `../legacy-streamlit/` so it no longer obscures the current app.

## ▶ Test the current app

**Live app:** https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

Current AppDeploy app ID: `elias-evidence-assistant-simscb`

The current product direction is one unified evidence-intelligence app: **Elias is the single user-facing intelligence engine, Evidence Auditor is its flagship audit workspace, and specialized capabilities remain behind the interface instead of becoming separate bots.**

The current build/snapshot includes:

- large searchable PDF indexing with visible progress
- OCR image intake and multimodal image/audio/video-frame analysis
- persistent case memory and multiple chat threads
- a persistent **Evidence Cloud** workspace for the shared case source library
- **Evidence Auditor** as the dedicated contradiction/gap/provenance/chronology/reviewer-readiness workspace
- a floating **Elias** assistant that stays the same identity everywhere and automatically changes its tool priorities based on the current workspace and request
- app-aware Copilot verbs: Find, Compare, Explain, Organize, Link, Draft, Build, Verify, and Export-preflight
- one-click Strongest Evidence, Missing Evidence, Contradiction Check, Timeline, C&P Rebuttal, and Packet QA passes
- Copilot **Create in one click** actions for Evidence Brief, C&P Rebuttal Draft, Hearing Timeline, and Full VA Packet
- Copilot result auto-scroll so the newest response remains visible and is marked **LATEST**
- a real local **Video + Motion Imaging** review player with scrub/playback, one-frame stepping, 0.25×–2× playback speed, and a one-click Motion Study
- explicit motion-analysis guardrails: a single 2D camera can support spatial/plane interpretation, but is not presented as calibrated medical 3D reconstruction
- a redesigned **Voice Studio** with Device vs. Neural engine status, delivery-style presets, voice selection, preview, stop, and auto-read replies
- a full manual Case Review workspace alongside the Copilot
- VA Law & Rater Lens with official-reference links
- public URL / YouTube research with explicit source boundaries
- optional live web search and neural voice when configured
- Packet Studio with one-click preflight, **One-click Create**, and full manual packet generation
- visible working/loading states that lock duplicate submissions while analysis is running

## Product architecture

**Elias** is the single intelligence engine and assistant.  
**Evidence Auditor** is the flagship evidence-audit feature/workspace.  
**Evidence Cloud** is the persistent case evidence layer.  
Health-record explanation, neurologic/functional review, citation verification, packet building, and document composition are **capabilities/lenses that Elias invokes internally**, not separate user-facing bots.

All capabilities use the same source-control rules and the same user-scoped evidence library. Generated summaries, tags, diagrams, interpretations, and packet prose must remain distinguishable from original source records.

The target evidence trace is:

`Source → page/locator → extracted evidence → evidence type → interpretation → generated statement`

See [ELIAS_EVIDENCE_CLOUD_V9_ROADMAP.md](./ELIAS_EVIDENCE_CLOUD_V9_ROADMAP.md) for the implementation/status boundary.

## Fast test path

1. Open the live app and sign in.
2. Add a searchable PDF or image and wait for **Ready**.
3. Open **Evidence Cloud** and confirm the same loaded record is visible there.
4. Open **Evidence Auditor** and run a contradiction/gap/provenance pass.
5. Open floating **Elias** from different workspaces and run **Strongest Evidence**; confirm Elias remains the same assistant while the workspace context changes.
6. Under **Create in one click**, try **Evidence Brief** or **Full VA Packet**.
7. Use **Media** to attach a short video. Review it in **Video + Motion Imaging**, change speed, step a frame, then run **Motion study**.
8. Open **Voice Studio**, preview a Device voice, and test Neural if it is connected.
9. Open **Packet Studio** and compare **One-click Create** with the full manual generation controls.

## Deployment note

The current production edition is deployed through AppDeploy and uses AppDeploy-provided auth, AI, storage, and API SDK capabilities. **The AppDeploy deployment is the authoritative production snapshot.** The `source/` directory is kept for public inspection and implementation reference as the product evolves.

The public repository remains privacy-safe: do not commit real VA claims, medical records, service records, claim numbers, private indexes, or personally identifying screenshots.

## Legacy implementation

The previous Streamlit code is preserved at [`../legacy-streamlit/`](../legacy-streamlit/) for reference and regression comparison. It is **not** the current production app.
