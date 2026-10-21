# Polyglot AI Stack Lab

A parallel learning project that shows **where each major language or format fits in a real AI/ML system**.

The goal is not to collect buzzwords. Each language has a concrete job in one small end-to-end workflow, so a reviewer can see both the code and the reason it exists.

## Core stack

| Technology | Role in the lab | Why it matters for AI/ML |
|---|---|---|
| Python | model/data logic | dominant language for ML, NLP, evaluation, notebooks, APIs |
| SQL | feature/data queries | nearly every production ML system depends on structured data retrieval |
| TypeScript | typed frontend logic | common for dashboards, review tools, human-in-the-loop interfaces |
| JavaScript | browser/runtime concepts | TypeScript compiles to JavaScript; useful for understanding web execution |
| Bash | automation | environment setup, repeatable commands, training/evaluation scripts |
| R | statistics | common in research, biostatistics, visualization, and validation |
| C++ | systems/performance | common under ML frameworks and for high-performance inference components |
| HTML/CSS | presentation | not programming languages, but essential for understandable web interfaces |
| JSON/JSONL | data interchange | common benchmark, API, and evaluation formats |
| YAML | configuration | common for CI/CD, experiments, and pipeline configuration |

## Optional/specialized later

- CUDA C++ for GPU kernels and low-level deep-learning performance
- Scala/Java for Spark and large-scale data engineering
- Go/Rust for production infrastructure and high-performance services

Those are valuable in some AI/ML jobs, but they are not universal prerequisites. We will add them only when the project has a real use for them.

## End-to-end story

```text
JSONL benchmark
      |
      v
Python preprocessing / ML
      |
      v
SQL feature + result store
      |
      v
R statistical analysis
      |
      v
C++ similarity/performance example
      |
      v
TypeScript review dashboard
      |
      v
HTML/CSS presentation
      |
      v
Bash + YAML automation
```

## Relationship to NeuroEval and Elias

- NeuroEval remains the AI/ML learning and evaluation lab.
- Elias remains the flagship evidence application.
- Polyglot AI Stack Lab explains the **software stack around AI/ML**.
- Proven components can move into NeuroEval or Elias when they solve a real problem.

## Portfolio rule

A technology is only counted as hands-on experience after AJ can:
1. explain what its component does;
2. run or test it;
3. make a small change;
4. explain why that technology was chosen over an alternative.

This repository work is project experience, not paid employment.
