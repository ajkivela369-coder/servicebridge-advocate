# Elias + Evidence Auditor — Build + Upgrade History

1. Started with a standalone Streamlit evidence-audit implementation and preserved it as legacy history.
2. Reframed the product as one user-facing Elias engine with Evidence Auditor as the flagship workspace.
3. Added Evidence Cloud, persistent case memory, source/page provenance, chronology, contradiction/gap review, and packet workflows.
4. Added multimodal document/media intake, motion review, Voice Studio, VA-law references, and packet preflight/create flows.
5. Added reviewable smart metadata and SHA-256 indexed-content fingerprints for duplicate handling.
6. Synced the current v0.5.6 Forge implementation and workflows into the portfolio source snapshot.
7. Added regression tests, public deployment checks, and explicit privacy/source-control boundaries.
8. Current boundary: AppDeploy is the authoritative production snapshot; the public repository must never contain real claimant records or private evidence.
## 2026-10-05 — On-demand PDF runtime / startup performance

- Moved PDF.js and its worker behind a shared on-demand loader so ordinary app startup no longer initializes document-rendering code.
- Moved submission-PDF composition behind a dynamic import so jsPDF and its helper chunks load only when a packet is actually composed.
- Preserved large-PDF ingestion, source-page rendering, Simple-mode PDF validation/preview, worker configuration, and the under-5-MB packet optimization workflow.
- Verification: `npx tsc --noEmit` passed; `npm run build` passed. The main production JS chunk is now ~374 kB; PDF parsing and submission composition are separate lazy chunks (~365 kB and ~406 kB respectively, plus their dependency chunks).
