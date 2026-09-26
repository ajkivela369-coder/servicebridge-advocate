# NeuroEval — Biology & Neuroscience AI Response Evaluator

An auditable evaluation harness for reviewing AI-generated biology and neuroscience answers. It demonstrates the core work of AI evaluation: define a rubric, make judgments reproducible, flag unsupported certainty, quantify benchmark behavior, and return structured reviewer output.

## Capabilities

- Biology/neuroscience domain evaluation
- Required-concept coverage checks
- Mechanistic-reasoning scoring
- Calibrated-uncertainty and overconfidence flags
- Evidence-language awareness
- Clarity scoring
- Structured JSON output
- Interactive Streamlit dashboard
- Extended labeled benchmark set
- Confusion-matrix/accuracy reporting
- Unit tests and GitHub Actions CI

The baseline is deliberately deterministic rather than pretending a model judge is ground truth. A production version could layer expert review, retrieval, or an LLM judge on top while preserving this baseline for auditability.

## Quick start

```bash
pip install -e .
neuroeval "Action potentials propagate because voltage-gated sodium channels open, followed by potassium-mediated repolarization. Evidence supports this mechanism, although kinetics vary across cell types." --concept "sodium channels" --concept potassium --concept repolarization
pytest -q
python metrics.py
```

## Interactive dashboard

```bash
pip install -r requirements-dashboard.txt
streamlit run dashboard.py
```

The dashboard exposes the rubric dimensions, deterministic flags, reviewer strengths, and downloadable JSON so evaluation decisions are easy to inspect and discuss.

## Benchmarking

`data/benchmark_extended.jsonl` includes labeled examples spanning action potentials, synaptic plasticity, microglia, myelination, blood-brain barrier biology, and dopamine signaling. `metrics.py` maps evaluator scores to PASS / REVIEW / FAIL buckets and prints accuracy plus a confusion matrix against the labels.

## Why this matters

High-quality AI evaluation is more than deciding whether an answer sounds right. Reviewers need repeatable criteria, explicit uncertainty, traceable failure modes, benchmark cases, and examples that can be compared across models. NeuroEval turns those expectations into a compact reference implementation.

## Scope

Portfolio and research demonstration only. This is not a diagnostic or clinical decision-support system and does not provide patient-specific medical advice.

## Live deployment

https://neuroeval-t6k31i.v2.appdeploy.ai/

This is the current public portfolio deployment for **NeuroEval**.


## AI/ML learning track

NeuroEval is also being used as a transparent AI/ML learning project. The first ML layer adds a
classical NLP baseline using TF-IDF text features, logistic-regression classification,
stratified cross-validation, precision/recall/F1, confusion matrices, and TF-IDF retrieval.

Run the experiment:

```bash
pip install -e .
python ml_experiment.py
```

See [AI_ML_LEARNING_TRACK.md](AI_ML_LEARNING_TRACK.md) for the concepts, limitations, and planned
embedding/deep-learning stages. The current benchmark is small, so its metrics are demonstration
results rather than production-performance claims.


## Visual AI/ML Lab

The Streamlit dashboard now works as a guided visual lab rather than only a scoring form. Each step
pairs a plain-English visual with the code that produces it, then explains why the concept matters.

Current walkthrough:

1. benchmark cases and labels;
2. rule-based text signals;
3. TF-IDF feature engineering;
4. logistic-regression training and prediction probabilities;
5. stratified cross-validation;
6. accuracy, precision, recall, F1, and confusion matrices;
7. held-out error analysis;
8. TF-IDF/cosine-similarity retrieval;
9. a portfolio learning summary and explicit next stages.

Run it with:

```bash
pip install -e .
pip install -r requirements-dashboard.txt
streamlit run dashboard.py
```

The dashboard deliberately distinguishes what is implemented today from future work. Sentence
embeddings and PyTorch deep learning are shown as next stages, not as completed capabilities.
