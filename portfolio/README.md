# AJ AI Evaluation Lab

Seven compact, auditable applications demonstrating practical AI-evaluation work across neuroscience, health-science safety, evidence review, pairwise preference evaluation, citation QA, annotation calibration, and benchmark authoring.

## Applications

### [NeuroEval](handshake-neuroeval/)
Biology and neuroscience response evaluation with transparent scoring for concept coverage, mechanistic reasoning, uncertainty calibration, evidence language, clarity, and unsupported certainty.

### [HealthQA Auditor](meridial-healthqa/)
Safety-first health-science AI output auditing with PASS / REVIEW / ESCALATE dispositions, patient-specific claim detection, dosing-language flags, urgent-symptom escalation checks, and machine-readable reviewer output.

### [Evidence Auditor](evidence-auditor/)
Privacy-safe benefits/disability evidence intelligence with issue mapping, favorable/unfavorable/mixed/neutral classification, missing-record signals, contradiction pairing, evidence matrices, and reviewer JSON. Synthetic or de-identified examples only.

### [PairRank](pairrank/)
Pairwise LLM-response evaluation with weighted rubrics, A/B preference labels, failure tags, reviewer notes, written justification, and JSON export.

### [CiteGuard](citeguard/)
Scientific claim-to-source auditing with claim/source mapping, lexical-support triage, overclaim detection, weak-support routing, and structured audit export. It explicitly distinguishes source matching from truth verification.

### [RaterLab](raterlab/)
Annotation quality assurance and reviewer calibration with gold-set accuracy, inter-rater agreement, Cohen's kappa, disagreement queues, label-distribution inspection, and calibration exports.

### [Benchmark Forge](benchmark-forge/)
Structured AI benchmark authoring for prompts, expected concepts, prohibited misconceptions, difficulty, gold labels, reviewer rationales, coverage reporting, and JSON/JSONL export.

## Design principles

- Transparent, inspectable baselines rather than hidden claims of model intelligence.
- Human review remains explicit in every high-stakes workflow.
- Machine-readable outputs support reproducible evaluation and QA.
- Portfolio examples use synthetic or de-identified data where privacy matters.
- Projects are demonstrations of hands-on AI-evaluation work, not claims of paid AI employment or production clinical/legal systems.

## Road to 12

The portfolio is being built as a coherent evaluation lab rather than a collection of unrelated demos. Future apps can extend into prompt-adversarial testing, multimodal/document-output QA, model regression testing, evaluation analytics, and workflow-quality review.
