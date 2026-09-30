# Elias + Evidence Auditor — Build + Upgrade History

1. Started with a standalone Streamlit evidence-audit implementation and preserved it as legacy history.
2. Reframed the product as one user-facing Elias engine with Evidence Auditor as the flagship workspace.
3. Added Evidence Cloud, persistent case memory, source/page provenance, chronology, contradiction/gap review, and packet workflows.
4. Added multimodal document/media intake, motion review, Voice Studio, VA-law references, and packet preflight/create flows.
5. Added reviewable smart metadata and SHA-256 indexed-content fingerprints for duplicate handling.
6. Synced the current v0.5.6 Forge implementation and workflows into the portfolio source snapshot.
7. Added regression tests, public deployment checks, and explicit privacy/source-control boundaries.
8. Current boundary: AppDeploy is the authoritative production snapshot; the public repository must never contain real claimant records or private evidence.