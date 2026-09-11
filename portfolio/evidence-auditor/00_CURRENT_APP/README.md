# Elias Evidence Auditor Pro — CURRENT APP

> **Start here.** This folder points to the current production build. The older Streamlit implementation has been moved under `../legacy-streamlit/` so it no longer obscures the current app.

## ▶ Test the current app

**Live app:** https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

Current AppDeploy app ID: `elias-evidence-assistant-simscb`

The current build is a signed-in, source-grounded evidence workspace with:

- large searchable PDF indexing with visible progress
- OCR image intake and multimodal image/audio/video-frame analysis
- persistent case memory and multiple chat threads
- floating **Elias Copilot** with one-click Strongest Evidence, Missing Evidence, Contradiction Check, Timeline, C&P Rebuttal, and Packet QA passes
- a full manual Case Review workspace alongside the Copilot
- VA Law & Rater Lens with official-reference links
- public URL / YouTube research with explicit source boundaries
- optional live web search and neural voice when configured
- Voice Studio controls with browser/device fallback
- Packet Studio with one-click preflight plus full manual packet generation
- visible working/loading states that lock duplicate submissions while analysis is running

## Fast test path

1. Open the live app and sign in.
2. Add a searchable PDF or image.
3. Wait for the upload card to show **Ready**.
4. Open the floating **Elias Copilot** and click **Strongest Evidence** or **Contradiction Check**.
5. Open **Case Review** for structured evidence, law, gap, and source-inventory tools.
6. Open **Packet Studio** and run **One-click preflight** before generating a draft.

## Deployment note

The current production edition is deployed through AppDeploy and uses AppDeploy-provided auth, AI, storage, and API SDK capabilities. The AppDeploy deployment is the source of truth for the current production build.

The public repository remains privacy-safe: do not commit real VA claims, medical records, service records, claim numbers, private indexes, or personally identifying screenshots.

## Legacy implementation

The previous Streamlit code is preserved at [`../legacy-streamlit/`](../legacy-streamlit/) for reference and regression comparison. It is **not** the current production app.
