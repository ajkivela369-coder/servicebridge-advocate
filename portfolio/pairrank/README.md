# PairRank

PairRank is a pairwise LLM-response evaluation workspace for comparing two model outputs against a weighted rubric.

It demonstrates:
- criterion-weighted scoring across accuracy, relevance, reasoning, clarity, and safety;
- A/B preference labeling;
- failure-mode tagging;
- reviewer notes and written justification;
- machine-readable JSON export.

This mirrors common human-evaluation and RLHF-style review tasks while keeping the final judgment explicitly human-authored.

## Run

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit deployment

Main file path:

`portfolio/pairrank/dashboard.py`

Portfolio/research demonstration only.
