# NeuroEval — Biology & Neuroscience AI Response Evaluator

An auditable evaluation harness for reviewing AI-generated biology and neuroscience answers. It demonstrates the core work of AI evaluation: define a rubric, make judgments reproducible, flag unsupported certainty, and return structured reviewer output.

## Capabilities

- Biology/neuroscience domain evaluation
- Required-concept coverage checks
- Mechanistic-reasoning scoring
- Calibrated-uncertainty and overconfidence flags
- Evidence-language awareness
- Clarity scoring
- Structured JSON output
- Unit tests and sample benchmark cases

The baseline is deliberately deterministic rather than pretending a model judge is ground truth. A production version could layer expert review, retrieval, or an LLM judge on top while preserving this baseline for auditability.

## Quick start

```bash
pip install -e .
neuroeval "Action potentials propagate because voltage-gated sodium channels open, followed by potassium-mediated repolarization. Evidence supports this mechanism, although kinetics vary across cell types." --concept "sodium channels" --concept potassium --concept repolarization
pytest -q
```

## Why this matters

High-quality AI evaluation is more than deciding whether an answer sounds right. Reviewers need repeatable criteria, explicit uncertainty, traceable failure modes, and examples that can be compared across models. NeuroEval turns those expectations into a compact reference implementation.

## Scope

Portfolio and research demonstration only. This is not a diagnostic or clinical decision-support system and does not provide patient-specific medical advice.
