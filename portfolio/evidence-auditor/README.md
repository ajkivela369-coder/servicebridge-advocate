# Evidence Auditor

A privacy-safe portfolio demonstration for reviewing benefits/disability case evidence with transparent, deterministic rules and human-review routing.

## What it demonstrates

- Sentence-level evidence extraction
- Favorable / unfavorable / mixed / neutral stance labeling
- Lightweight source-type inference (medical, service, lay, administrative)
- Confidence and rationale for every flag
- Potential contradiction/tension detection
- Machine-readable reviewer JSON
- Streamlit reviewer dashboard

The project is inspired by real-world document-review workflows but **does not contain personal VA claim records, medical records, service records, names, claim numbers, or other private source material**. Included examples are synthetic.

## Why this project exists

Large administrative cases often contain many documents that disagree, omit context, or use different language for the same issue. Evidence Auditor shows how an AI-assisted review workflow can organize passages for a human reviewer without pretending that keyword rules can make a legal or benefits determination.

Every automated classification is inspectable. The reviewer is expected to verify each conclusion against the underlying source and governing rules.

## Run locally

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit deployment

Use this main file path in Streamlit Community Cloud:

`portfolio/evidence-auditor/dashboard.py`

## Current limitations

This baseline is deliberately deterministic. It does not establish legal relevance, verify medical truth, determine service connection, calculate benefits, or replace an attorney, accredited representative, clinician, or adjudicator. Keyword-based stance detection can miss nuanced language, and contradiction detection is only a screening aid.

## Planned v2

- document/page/source provenance fields
- timeline reconstruction
- semantic issue clustering
- reference-backed contradiction analysis
- missing-record/gap detection
- human reviewer corrections and adjudication notes
- batch JSONL/CSV review
- benchmark metrics and regression tests

Portfolio/research demonstration only; not legal advice or a benefits decision engine.
