# Elias + Elias Build Lab — Two-App Architecture

## Product decision

The portfolio now has two primary applications with different jobs:

### Elias
The production/performance application.

Elias should prioritize:
- reliability;
- evidence grounding;
- provenance;
- privacy;
- retrieval quality;
- user-facing workflows;
- clear status/limitations;
- tested features only.

Experimental AI/ML features do not move into Elias merely because they are newer or more complex.

### Elias Build Lab
The educational and experimental twin.

Build Lab should:
- explain how Elias works;
- teach the AI/ML and software concepts behind it;
- host visual experiments;
- compare candidate techniques;
- document failures and tradeoffs;
- provide portfolio evidence of hands-on learning;
- use synthetic/de-identified data only.

NeuroEval, EvidencePipe, and future ModelForge experiments are learning tracks/modules inside Build Lab rather than additional flagship products.

## Promotion path

```text
Learn concept
    ↓
Build experiment in Elias Build Lab
    ↓
Create measurable benchmark
    ↓
Test + inspect failure cases
    ↓
Compare with current Elias method
    ↓
Does it improve Elias?
    ├── No → keep as learning/research artifact
    └── Yes
         ↓
      regression tests
         ↓
      privacy/provenance review
         ↓
      production integration
         ↓
        Elias
```

## Shared design rule

Build Lab may explain and experiment with:
- NLP
- machine learning
- embeddings
- RAG
- deep learning
- data engineering
- model evaluation
- human-in-the-loop review
- TypeScript/frontend patterns
- testing and CI

Elias receives only the subset that improves the production system.

## Evidence boundary

Both applications should preserve the evidence trace:

**Source → page/locator → extracted evidence → evidence classification → interpretation → generated statement**

Evidence classifications must remain distinguishable:
- exact quote
- paraphrase
- claimant-reported history
- clinician observation
- objective test
- medical opinion
- agency finding
- AI/analyst synthesis

Build Lab must use only synthetic/de-identified examples. It is not a medical device.

## Portfolio framing

A skill counts as hands-on project experience only when the learner can:
1. explain the concept;
2. run the implementation;
3. make a small change;
4. interpret the output;
5. describe an important limitation.

This architecture is intended to make learning visible without overstating paid employment or expertise.
