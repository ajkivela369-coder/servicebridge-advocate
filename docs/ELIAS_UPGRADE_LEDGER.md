# Elias Upgrade Ledger

This ledger separates educational experiments from production adoption.

| Experiment / Capability | Build Lab status | Test status | Elias status | Evidence / Notes |
| --- | --- | --- | --- | --- |
| Evidence provenance trace | Implemented concept | Existing regression coverage in Elias development | Implemented / expanding | Core production requirement |
| TF-IDF retrieval | Implemented in NeuroEval learning branch | Classical baseline under test | Evaluation only | Useful lexical baseline |
| Logistic regression PASS/REVIEW/FAIL | Implemented in NeuroEval learning branch | Cross-validation + metrics | Lab only | Teaches supervised ML; not a production need by default |
| Error-analysis dashboard | Implemented in NeuroEval learning branch | Visual review workflow | Lab only | Portfolio/evaluation tool |
| Sentence embeddings | Planned | Not yet benchmarked | Not adopted | Must beat retrieval baseline on fixed queries before promotion |
| Semantic retrieval | Planned | Not yet benchmarked | Not adopted | Evaluate relevant-source recall and false matches |
| PyTorch text classifier | Planned | Not yet implemented | Not adopted | Deep-learning learning track; compare against classical ML |
| RAG comparison harness | Planned | Not yet implemented | Existing Elias retrieval remains production baseline | Compare grounded-answer quality and citation trace |
| EvidencePipe data-quality checks | Prototype / learning branch | Tests added in branch | Candidate | Promote only checks that improve source integrity without silent mutation |
| Human approval gates | Core design principle | Existing feature-specific checks | Implemented / expanding | Generated interpretation must remain distinguishable from original evidence |

## Status meanings

- **Implemented** — code exists in the named environment.
- **Lab only** — useful for learning/evaluation; not a production claim.
- **Candidate** — may move into Elias after validation.
- **Planned** — not implemented and must not be represented as complete.
- **Adopted** — tested and integrated into Elias production/development architecture.

## Promotion checklist

A lab experiment should not move into Elias until:
- the comparison benchmark is defined;
- baseline and candidate use the same test cases;
- failure cases are inspected;
- output provenance remains traceable;
- privacy boundaries remain intact;
- regression tests exist;
- the change improves a user-relevant metric or workflow;
- documentation clearly describes remaining limitations.
