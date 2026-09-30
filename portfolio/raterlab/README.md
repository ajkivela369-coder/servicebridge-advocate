# RaterLab

RaterLab is an annotation-QA and reviewer-calibration dashboard.

It demonstrates:
- gold-set accuracy scoring;
- inter-rater agreement;
- Cohen's kappa;
- disagreement queues;
- label-distribution drift inspection;
- JSON and CSV calibration exports.

These are practical quality-control concepts used in human annotation and AI-evaluation programs.

## Build + upgrade history

See [BUILD_AND_UPGRADE.md](BUILD_AND_UPGRADE.md) for the step-by-step implementation and QC trail.

## Required CSV columns

`item_id,gold,rater_a,rater_b`

## Run

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## Streamlit deployment

Main file path:

`portfolio/raterlab/dashboard.py`