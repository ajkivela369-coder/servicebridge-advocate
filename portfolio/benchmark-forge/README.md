# Benchmark Forge

Benchmark Forge is a structured benchmark-authoring app for AI evaluation.

It lets a reviewer create and export evaluation items containing:
- prompt and domain;
- difficulty;
- expected concepts;
- prohibited misconceptions;
- gold disposition;
- reviewer rationale.

It also reports dataset coverage and validation gaps and exports JSON/JSONL suitable for downstream evaluation pipelines.

## Run

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit deployment

Main file path:

`portfolio/benchmark-forge/dashboard.py`
