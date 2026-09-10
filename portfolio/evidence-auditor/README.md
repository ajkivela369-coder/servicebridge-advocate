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
- Same-issue supporting/adverse evidence pairing for human rebuttal review
- Reviewer-supplied mechanism / sequence mapping
- Screenshot and diagram upload for visual exhibits
- **Two generated PDF styles**
  - **Visual Claim Packet** — color, evidence cards, mechanism map, visual exhibits, rebuttal desk, appendix
  - **Formal Evidence Review** — restrained professional styling for conservative handoff
- Reviewer JSON export

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

## Public-demo privacy boundary

This repository is intentionally public-safe. Do not commit real medical records, VA claim files, claim numbers, service records, private indexes generated from a real case, or screenshots containing real personal identifiers. Use fictional or thoroughly de-identified examples for public demos.

Uploaded PDFs/images are processed by the running Streamlit session. Hosting/provider retention rules still apply; do not use a public deployment for sensitive records unless its deployment and data-handling controls are appropriate for that use.

## Review philosophy

Evidence Auditor Pro helps a human reviewer find and organize evidence; it does **not** decide a claim. A quotation match does not prove authenticity, medical truth, or legal significance. A tension flag is a routing aid, not a finding that an examiner or adjudicator is wrong.

Mechanism maps are reviewer-supplied explanatory organization. The app does not silently infer medical causation.

## Current limitations

- Scanned/image-only PDFs require OCR before text extraction in this public baseline.
- Quote verification is normalized exact matching, not semantic quotation reconstruction.
- It does not independently determine duty status, service connection, diagnostic validity, rating percentage, eligibility, or legal sufficiency.
- Visual exhibits are reviewer supplied; the public repo does not ship private screenshots.
