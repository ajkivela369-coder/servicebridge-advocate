# Evidence Auditor Pro

A privacy-safe, source-backed evidence review and packet-building demonstration for complex medical, service, legal, disability-benefit, and administrative records.

The public repository contains **fictional examples only**. It does not contain private VA records, medical records, service records, names, claim numbers, or private case indexes.

## Recommended workflow

1. **Start with Elias.** Upload the source PDFs once, let the session build the page-level evidence workspace, ask source-grounded questions, and create a first evidence-packet draft.
2. **Use the focused review pages** when you want to inspect one quality dimension in detail.
3. **Use the floating ✦ Copilot** from review pages for quick questions without leaving the current workspace.
4. **Human-review the result** before anything is filed or shared externally.

## Workspace guide

- **Elias · Start Here** — the primary intake and assistant workspace. Load the record, inspect the evidence summary, ask Elias questions, and generate a first reviewer-ready packet draft.
- **Review Readiness** — checks whether sources are locatable and usable: source names, page locators, extractable text, and provenance quality.
- **Quote Integrity** — verifies proposed verbatim quotations against the loaded source text and keeps unresolved quotations visibly unresolved.
- **Packet Integrity** — checks whether a proposed packet stays traceable to the source record and whether key packet components are internally consistent.
- **Coverage Gaps** — highlights issues, evidence categories, or source types that appear thin or missing so a reviewer knows what to investigate next.
- **Packet Assurance** — combines provenance, evidence coverage, and quote integrity into a transparent reviewer-readiness screen. It is not a merits score.
- **Source Inventory** — gives the reviewer a source-centered view of what is loaded and where important evidence came from.
- **Floating Copilot** — a lower-right ✦ assistant available from review pages. It gives quick source-grounded answers and links back to Elias; it is intentionally not a separate sidebar destination.

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
- **Floating Evidence Copilot** — a lower-right support panel that uses the current session audit, preserves source/page locators, and declines unsupported questions rather than guessing
- **Elias**, now the first reviewer workspace, with one-place PDF intake, citation-first evidence interrogation, source-gap review, tension analysis, first-draft packet generation, and browser voice preview
- Browser voice preview for Elias with a default **Younger Distinguished** profile: measured authority, crisp diction, slightly brighter timbre, and restrained warmth
- **Two generated PDF styles**
  - **Visual Claim Packet** — color, evidence cards, mechanism map, visual exhibits, rebuttal desk, appendix
  - **Formal Evidence Review** — restrained professional styling for conservative handoff
- Reviewer JSON export

## Copilot vs. Elias

**Elias** is the main workspace and starting point. Use it when you want to load a record, interrogate the evidence deeply, find gaps and contradictions, or generate a first packet draft.

**Evidence Copilot** is the quick support layer. Use the floating ✦ launcher while working in a review page. It intentionally stays out of the sidebar so it behaves like a true in-context copilot instead of a competing destination.

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

The multipage app exposes Elias first, followed by the focused review workspaces. The Evidence Copilot is rendered as a floating launcher rather than a separate navigation page.

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