# Elias Build Lab

Educational/experimental twin of Elias Evidence Auditor.

- Elias stays production/performance focused.
- Build Lab teaches and tests the AI/ML, retrieval, data-engineering, and software concepts behind Elias.
- NeuroEval and EvidencePipe are learning tracks inside Build Lab.
- Lab techniques are promoted only after benchmarking, error review, tests, and production safeguards.

The current MVP includes visual side-by-side lessons for architecture, Evidence Cloud/data engineering, NLP/TF-IDF, supervised ML, model evaluation, retrieval/RAG, a build timeline, upgrade ledger, and a local study checklist.

All examples are synthetic/de-identified. This is a learning/portfolio application, not a medical device.


## TF-IDF vs sentence embeddings

Build Lab now includes a real side-by-side retrieval experiment:

- **TF-IDF** is implemented locally in TypeScript as a sparse lexical baseline.
- **Sentence embeddings** run in the browser through `@huggingface/transformers` using
  `onnx-community/all-MiniLM-L6-v2-ONNX`.
- Both methods rank the same synthetic neuroscience passages for the same query.
- The first embedding run downloads the model; later runs reuse the loaded model and cached document vectors.
- Embeddings remain a **lab experiment** until a fixed retrieval benchmark shows a useful improvement over the baseline.

This distinction is intentional: a newer model is not promoted into Elias unless it improves a user-relevant metric while preserving provenance and acceptable false-match behavior.
