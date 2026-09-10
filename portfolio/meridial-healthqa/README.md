# HealthQA Auditor — Safety-First Health-Science AI Evaluation

A reviewer-oriented quality and safety harness for AI-generated health-science content. The project demonstrates how an evaluator can separate content quality from clinical-risk signals, produce structured labels, and route questionable outputs to human review.

## Capabilities

- Health-science content QA
- Patient-safety risk detection
- Dosing/prescribing-language flags
- Patient-specific diagnostic-certainty flags
- Emergency-language escalation checks
- Overconfidence detection
- PASS / REVIEW / ESCALATE dispositions
- Machine-readable audit output
- Benchmark cases and automated tests

The goal is not to diagnose patients. It is to evaluate whether AI-generated health content should pass, be reviewed, or be escalated.

## Quick start

```bash
pip install -e .
healthqa "Chest pain can have many causes. If it is severe or accompanied by difficulty breathing, seek urgent medical evaluation."
pytest -q
```

## Evaluation philosophy

A useful health-content evaluator should be conservative about patient-specific claims, explain why something was flagged, and make escalation explicit. This repo uses deterministic checks as an auditable baseline and keeps the architecture simple enough to extend with expert review, retrieval, or model-based judging.

## Scope

Portfolio and research demonstration only. This software is not medical advice, diagnosis, triage, treatment software, or a medical device and should not be used to make patient-care decisions.
