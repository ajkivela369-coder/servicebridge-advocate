# Elias Evidence Auditor Pro — CURRENT APP

> **Start here.** This folder points to the current production build. The older Streamlit implementation lives under `../legacy-streamlit/` so it no longer obscures the current app.

## ▶ Test the current app

**Live app:** https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

Current AppDeploy app ID: `elias-evidence-assistant-simscb`

The current build is a signed-in, source-grounded evidence workspace with:

- large searchable PDF indexing with visible progress
- OCR image intake and multimodal image/audio/video-frame analysis
- persistent case memory and multiple chat threads
- floating **Elias Copilot** with one-click Strongest Evidence, Missing Evidence, Contradiction Check, Timeline, C&P Rebuttal, and Packet QA passes
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

## Fast test path

1. Open the live app and sign in.
2. Add a searchable PDF or image and wait for **Ready**.
3. Open **Elias Copilot** and run **Strongest Evidence**.
4. Under **Create in one click**, try **Evidence Brief** or **Full VA Packet**.
5. Use **Media** to attach a short video. Review it in **Video + Motion Imaging**, change speed, step a frame, then run **Motion study**.
6. Open **Voice Studio**, preview a Device voice, and test Neural if it is connected.
7. Open **Case Review** for structured evidence, law, gap, and source-inventory tools.
8. Open **Packet Studio** and compare **One-click Create** with the full manual generation controls.

## Deployment note

The current production edition is deployed through AppDeploy and uses AppDeploy-provided auth, AI, storage, and API SDK capabilities. **The AppDeploy deployment is the authoritative production snapshot.** The `source/` directory is kept for public inspection and implementation reference as the product evolves.

The public repository remains privacy-safe: do not commit real VA claims, medical records, service records, claim numbers, private indexes, or personally identifying screenshots.

## Legacy implementation

The previous Streamlit code is preserved at [`../legacy-streamlit/`](../legacy-streamlit/) for reference and regression comparison. It is **not** the current production app.
