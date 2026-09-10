# CiteGuard

CiteGuard is a scientific claim-to-source auditing demo.

It maps individual claims to source snippets, estimates lexical coverage, flags absolute/overconfident language, routes weakly supported claims for review, and exports a structured audit record.

The project intentionally distinguishes **source matching** from **truth verification**: lexical overlap can help triage claims but cannot establish factual correctness.

## Run

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit deployment

Main file path:

`portfolio/citeguard/dashboard.py`

Portfolio/research demonstration only.
