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


## Retrieval benchmark

The semantic-retrieval lesson now has a fixed 50-query benchmark with human-defined relevant
passages. TF-IDF and sentence embeddings are scored against the same documents, queries, and
relevance labels.

Current metrics:
- **Hit@1** — correct source ranked first;
- **Recall@3** — relevant source appears in the top three;
- **MRR** — mean reciprocal rank of the first relevant source.

The benchmark intentionally includes both direct vocabulary queries and semantic paraphrases. This
creates a measurable promotion gate: sentence embeddings remain a Build Lab experiment until they
show a useful retrieval improvement and their false matches are reviewed.


## Dataset Lab

The first benchmark expansion increases the retrieval dataset from **5 passages / 10 queries** to
**25 passages / 50 queries** across ten neuroscience topics.

Each query now carries:
- topic;
- query family;
- query style (direct, paraphrase, mechanism, indirect, or multi-source);
- difficulty;
- one or more human-defined relevant passage IDs;
- a short rationale.

Dataset Lab visualizes topic/style/difficulty coverage and validates missing relevance IDs, exact
normalized duplicates, unused distractor passages, average query/document length, and
multi-passage relevance. It also exposes a review-first candidate expansion queue. Generated or
templated variants are never treated as gold labels automatically.

This is the first dataset-engineering stage. A larger PASS / REVIEW / FAIL classifier dataset and
grouped train/validation/test splitting are next; paraphrase families should remain entirely within
one split to reduce leakage.


## Classifier dataset

Build Lab now includes a deterministic **300-example synthetic classification dataset** for the
future logistic-regression-vs-PyTorch comparison.

Structure:
- 100 PASS
- 100 REVIEW
- 100 FAIL
- 50 concept families
- 10 neuroscience topics
- 2 variants of each label per family
- 180 train / 60 validation / 60 locked test examples

The split happens at the **family level**, not the row level. All six examples belonging to a
concept family stay together, which reduces paraphrase leakage across train, validation, and test.

Each example records:
- family ID;
- topic and concept;
- label;
- rationale;
- difficulty;
- failure mode;
- split;
- synthetic source status;
- review status.

The current examples are explicitly marked **template_generated**, not human-reviewed gold labels.
Dataset Lab audits label balance, family leakage, duplicates, missing rationales, and family label
coverage. A human-reviewed gold subset should be created before treating model metrics as strong
claims about generalization.


## Agent orchestration

Build Lab now includes an interactive **Model Router + Tool Registry + Agent Planner** prototype.

The model router demonstrates a three-tier policy:
- deterministic code for exact, auditable operations such as dates, quotes, source links, and packet assembly;
- smaller/local specialized models for semantic retrieval and narrow ML tasks;
- frontier LLMs for synthesis, comparison, and complex natural-language reasoning.

The tool registry currently models lexical search, semantic search, Claim → Source Trace,
contradiction review, timeline construction, quote verification, authority verification, reasoning,
packet building, and packet QA.

The planner converts natural-language goals into ordered tool steps and marks consequential packet
write/export steps with a **human approval** gate. This is a Build Lab prototype, not a claim that
the production Elias agent has already adopted autonomous orchestration.


## Planner benchmark

Build Lab now includes a fixed **45-case agent-planner benchmark** covering:

- exact lookup / quote / page tasks;
- semantic retrieval;
- timelines and chronologies;
- contradiction review;
- authority verification;
- grounded synthesis;
- packet workflows;
- failure-handling cases where Elias should stop rather than fabricate, erase, or guess evidence.

Each case defines the expected:
- model tier;
- ordered tool sequence;
- human approval tools;
- provenance requirement;
- stop behavior.

The dashboard scores model-route accuracy, tool precision/recall/F1, sequence order, exact-plan
accuracy, unnecessary-tool rate, approval gates, provenance preservation, stop behavior, and a
weighted overall score. This intentionally exposes weaknesses in the current simple keyword planner
before any smarter routing is promoted into production Elias.


## Veteran Advocacy Mode

Build Lab now includes a candidate **Veteran Advocacy Mode** for VBA-facing evidence packets.

The design intentionally gives Elias more freedom **inside** the packet-building workflow:
- repeatedly search the evidence corpus;
- build an issue matrix;
- audit an adverse VBA decision against the cited record;
- identify favorable evidence, adverse evidence, and evidentiary gaps;
- verify configured official authority;
- build a source-backed rebuttal map;
- create and revise packet drafts;
- rerun citation, contradiction, completeness, and reviewer-readiness QA until the draft is ready.

The human-approval boundary is moved to the **final export / filing handoff** rather than every
internal draft step. This lets Elias do meaningful multi-step advocacy work without requiring the
veteran to micromanage every search and revision.

The advocacy constraint is equally explicit: Elias may argue strongly from the record, but it must
not fabricate facts, invent quotations, guess missing dates, hide or delete adverse evidence, or
state unsupported medical conclusions. Adverse evidence should be addressed, contextualized, or
rebutted when the record supports doing so.

“Help the veteran win” therefore means: produce the strongest truthful, well-organized,
source-traceable packet supported by the available evidence and verified authority. It is not an
outcome guarantee.
