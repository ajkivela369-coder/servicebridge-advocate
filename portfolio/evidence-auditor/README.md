# Evidence Auditor Pro

A privacy-safe, source-backed evidence review and packet-building demonstration for complex medical, service, legal, disability-benefit, and administrative records.

The public repository contains **fictional examples only**. It does not contain private VA records, medical records, service records, names, claim numbers, or private case indexes.

## What v2 adds

- Multi-PDF intake with page-level provenance
- Source/page locators on extracted passages
- Favorable / unfavorable / mixed / neutral evidence classification
- Medical, service, lay, and administrative source typing
- Issue mapping and record-gap signals
- Normalized exact quote verification against source-page text
- Contextual quote-integrity review and packet-integrity gating
- Same-issue supporting/adverse evidence pairing for human rebuttal review
- Evidence-coverage and review-readiness analysis
- Reviewer-supplied mechanism / sequence mapping
- Screenshot and diagram upload for visual exhibits
- **Elias**, a citation-first mini evidence assistant that answers from the current audit, surfaces source gaps and tension pairs, and keeps page locators attached
- Browser voice preview for Elias with a default **Younger Distinguished** profile: measured authority, crisp diction, slightly brighter timbre, and restrained warmth
- **Two generated PDF styles**
  - **Visual Claim Packet** — color, evidence cards, mechanism map, visual exhibits, rebuttal desk, appendix
  - **Formal Evidence Review** — restrained professional styling for conservative handoff
- Reviewer JSON export

## Elias voice note

The public test uses the browser's built-in speech-synthesis voices, so the exact speaker varies by device and operating system. The Younger Distinguished preset is a new synthetic voice direction; it is not intended to clone or impersonate a real speaker from a reference recording.

## Run locally

```bash
cd portfolio/evidence-auditor
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit Community Cloud

Main file:

```text
portfolio/evidence-auditor/dashboard.py
```

The multipage app automatically exposes Review Readiness, Quote Integrity, Packet Integrity, Coverage Gaps, and Elias in the Streamlit navigation.

## Public-demo privacy boundary

This repository is intentionally public-safe. Do not commit real medical records, VA claim files, claim numbers, service records, private indexes generated from a real case, or screenshots containing real personal identifiers. Use fictional or thoroughly de-identified examples for public demos.

Uploaded PDFs/images are processed by the running Streamlit session. Hosting/provider retention rules still apply; do not use a public deployment for sensitive records unless its deployment and data-handling controls are appropriate for that use.

## Review philosophy

Evidence Auditor Pro helps a human reviewer find and organize evidence; it does **not** decide a claim. A quotation match does not prove authenticity, medical truth, or legal significance. A tension flag is a routing aid, not a finding that an examiner or adjudicator is wrong.

Mechanism maps are reviewer-supplied explanatory organization. The app does not silently infer medical causation. Elias follows the same boundary: he is an evidence navigator, not legal or medical counsel.

## Current limitations

- Scanned/image-only PDFs require OCR before text extraction in this public baseline.
- Quote verification is normalized exact/contextual matching, not semantic quotation reconstruction.
- Elias is currently a deterministic local evidence assistant rather than a hosted general-purpose LLM.
- Browser speech synthesis differs across Chrome/Edge/macOS/Windows and cannot guarantee one identical voice everywhere.
- It does not independently determine duty status, service connection, diagnostic validity, rating percentage, eligibility, or legal sufficiency.
- Visual exhibits are reviewer supplied; the public repo does not ship private screenshots.
