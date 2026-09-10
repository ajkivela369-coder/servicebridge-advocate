# Evidence Auditor Pro

A privacy-safe, source-backed evidence review and packet-building demonstration for complex medical, service, legal, disability-benefit, and administrative records.

The public repository contains **fictional examples only**. It does not contain private VA records, medical records, service records, names, claim numbers, or private case indexes.

## Three-page design

Evidence Auditor Pro is intentionally reduced to three user-facing destinations:

1. **Elias** — the main ChatGPT-style workspace. Upload the record once, keep multiple chat threads, ask natural-language questions, use built-in evidence tools, maintain session-local case memory, and route the work into packet generation.
2. **Case Review** — the structured quality-control view. It combines provenance readiness, evidence review, quotation verification, issue coverage, contradictions, record-gap signals, and source inventory into one page.
3. **Packet Studio** — the final packet workspace. It combines packet assurance, visual/formal packet styles, proposed quotation checks, mechanism sequencing, rebuttal notes, visual exhibits, PDF export, and reviewer JSON export.

The default Streamlit navigation is hidden and replaced by this small three-destination shell so the app does not feel like a collection of disconnected utilities.

## Elias interaction model

Elias is the front door rather than a side feature.

- **Chat threads** — start a new chat and switch between session-local conversations from the sidebar.
- **One-place case intake** — PDFs, text, and Markdown are uploaded only in Elias and shared with Case Review and Packet Studio for the current session.
- **Session-local case memory** — Elias can keep a case label, goal, notes, and an automatically refreshed record summary. Memory can be disabled, exported to JSON, and imported into another session. The public demo does not pretend this is server-side persistent memory.
- **Built-in tools / plugins** — Record Search, Gap Finder, Quote Check, and Packet Assurance can be turned on or off. These are local evidence tools, not external account connections.
- **Transparent responses** — Elias can show source chips and the tools used for a response. Unsupported questions are declined rather than filled with invented evidence.
- **Quick Elias** — Case Review and Packet Studio keep a floating **Ask Elias** button so the user can ask a source-grounded question without leaving the current page.

## Evidence capabilities

- Multi-document intake with page-level provenance
- Source/page locators on extracted passages
- Favorable / unfavorable / mixed / neutral evidence classification
- Medical, service, lay, and administrative source typing
- Issue mapping and record-gap signals
- Normalized exact and contextual quote verification
- Same-issue supporting/adverse evidence pairing
- Evidence-coverage and provenance-readiness analysis
- Packet Assurance combining provenance, evidence depth, and quote integrity into a reviewer-workflow score
- Reviewer-supplied mechanism / sequence mapping
- Screenshot and diagram upload for visual exhibits
- Two generated PDF styles:
  - **VA Evidence Packet** / visual claim packet
  - **Formal Evidence Review**
- Reviewer JSON export

## Important boundary

Elias is designed to feel conversational, but the public baseline still uses a deterministic, local evidence-grounding engine rather than a hosted general-purpose LLM. The interface can support future model or connector integrations without changing the core provenance rules.

The built-in “plugins” are evidence-review modules inside the app. They do not represent connected Gmail, Drive, VA, medical-record, or other external accounts.

## Run locally

```bash
cd portfolio/evidence-auditor
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

Main Streamlit file:

```text
portfolio/evidence-auditor/dashboard.py
```

Do **not** run `copilot_engine.py`, `elias_plugins.py`, or `elias_memory.py` directly with Streamlit. They are shared backend modules.

## Public-demo privacy boundary

This repository is intentionally public-safe. Do not commit real medical records, VA claim files, claim numbers, service records, private indexes generated from a real case, or screenshots containing real personal identifiers. Use fictional or thoroughly de-identified examples for public demos.

Uploaded documents and images are processed by the running Streamlit session. Hosting/provider retention rules still apply; do not use a public deployment for sensitive records unless its deployment and data-handling controls are appropriate for that use.

## Review philosophy

Evidence Auditor Pro helps a human reviewer find and organize evidence; it does **not** decide a claim. A quotation match does not prove authenticity, medical truth, or legal significance. A tension flag is a routing aid, not a finding that an examiner or adjudicator is wrong.

Mechanism maps are reviewer-supplied explanatory organization. The app does not silently infer medical causation. Packet Assurance measures reviewer workflow quality, provenance, evidence depth, and quotation integrity—not the merits of a disability, legal, medical, or benefits claim.

## Current limitations

- Scanned/image-only PDFs require OCR before text extraction in this public baseline.
- Quote verification is normalized exact/contextual matching, not semantic quotation reconstruction.
- Elias currently uses a deterministic local evidence engine rather than a hosted general-purpose LLM.
- Case memory is session-local unless the user explicitly exports/imports the memory JSON.
- Built-in tools are local modules, not external service plugins or connectors.
- Packet Assurance uses transparent heuristic weights for reviewer readiness; its composite score is not a validated legal or clinical instrument.
- The app does not independently determine duty status, service connection, diagnostic validity, rating percentage, eligibility, or legal sufficiency.
- Visual exhibits are reviewer supplied; the public repo does not ship private screenshots.
