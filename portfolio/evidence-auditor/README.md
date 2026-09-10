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
- **Packet Assurance** — a unified reviewer trust layer combining provenance readiness, issue-coverage depth, and proposed verbatim-quote integrity into one non-merits readiness screen
- Reviewer-supplied mechanism / sequence mapping
- Screenshot and diagram upload for visual exhibits
- **Evidence Copilot** — an optional floating lower-right support panel plus a full interactive Copilot page. Both use the current session audit, preserve source/page locators, and decline unsupported questions rather than guessing.
- **Elias**, a separate citation-first evidence-assistant workspace for deeper record interrogation, source-gap review, tension analysis, and browser voice preview
- Browser voice preview for Elias with a default **Younger Distinguished** profile: measured authority, crisp diction, slightly brighter timbre, and restrained warmth
- **Two generated PDF styles**
  - **Visual Claim Packet** — color, evidence cards, mechanism map, visual exhibits, rebuttal desk, appendix
  - **Formal Evidence Review** — restrained professional styling for conservative handoff
- Reviewer JSON export

## Copilot vs. Elias

**Evidence Copilot** is the quick support layer. Use the floating ✦ launcher while working in Evidence Auditor Pro, or open the full Evidence Copilot page for a larger interactive workspace. Copilot and its page share the same session-local conversation history.

**Elias** remains a separate evidence-assistant experience with its own presentation and voice studio. The two surfaces share the same deterministic grounding boundary but serve different interaction styles.

The old `assistant_bot.py` entrypoint was intentionally removed. It was a backend helper, not a Streamlit page, and launching it directly could produce a blank navigation entry labeled “assistant bot.” The shared backend now lives in `copilot_engine.py`.

## Elias voice note

The public test uses the browser's built-in speech-synthesis voices, so the exact speaker varies by device and operating system. The Younger Distinguished preset is a new synthetic voice direction; it is not intended to clone or impersonate a real speaker from a reference recording.

## Run locally

```bash
cd portfolio/evidence-auditor
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

Do **not** run `copilot_engine.py` directly with Streamlit. It is a shared grounding engine, not an app entrypoint.

## Streamlit Community Cloud

Main file:

```text
portfolio/evidence-auditor/dashboard.py
```

The multipage app exposes Review Readiness, Quote Integrity, Packet Integrity, Coverage Gaps, Elias Assistant, Packet Assurance, and Evidence Copilot in the Streamlit navigation. The dashboard also includes the floating Evidence Copilot launcher.

## Public-demo privacy boundary

This repository is intentionally public-safe. Do not commit real medical records, VA claim files, claim numbers, service records, private indexes generated from a real case, or screenshots containing real personal identifiers. Use fictional or thoroughly de-identified examples for public demos.

Uploaded PDFs/images are processed by the running Streamlit session. Hosting/provider retention rules still apply; do not use a public deployment for sensitive records unless its deployment and data-handling controls are appropriate for that use.

## Review philosophy

Evidence Auditor Pro helps a human reviewer find and organize evidence; it does **not** decide a claim. A quotation match does not prove authenticity, medical truth, or legal significance. A tension flag is a routing aid, not a finding that an examiner or adjudicator is wrong.

Mechanism maps are reviewer-supplied explanatory organization. The app does not silently infer medical causation. Evidence Copilot and Elias follow the same boundary: they are evidence navigators, not legal or medical counsel. Packet Assurance likewise measures reviewer workflow quality, provenance, evidence depth, and quotation integrity—not the merits of a disability, legal, medical, or benefits claim.

## Current limitations

- Scanned/image-only PDFs require OCR before text extraction in this public baseline.
- Quote verification is normalized exact/contextual matching, not semantic quotation reconstruction.
- Evidence Copilot and Elias currently use a deterministic local evidence engine rather than a hosted general-purpose LLM.
- Browser speech synthesis differs across Chrome/Edge/macOS/Windows and cannot guarantee one identical voice everywhere.
- Packet Assurance uses transparent heuristic weights for reviewer readiness; its composite score is not a validated legal or clinical instrument.
- It does not independently determine duty status, service connection, diagnostic validity, rating percentage, eligibility, or legal sufficiency.
- Visual exhibits are reviewer supplied; the public repo does not ship private screenshots.
