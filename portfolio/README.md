# AJ AI Evaluation Lab

A growing collection of compact, auditable AI applications spanning neuroscience, health-science safety, evidence review, pairwise preference evaluation, citation QA, annotation calibration, benchmark authoring, and creative media production.

<!-- FORGE-SUITE-PORTFOLIO:START -->
## Current integrated Forge Suite

The newest integrated implementation is **Forge v0.5.6+**, mirrored at **[`../forge-suite/current/`](../forge-suite/current/)**. It unifies Forge Workspace, Elias, Evidence Auditor, MedForge, GrimForge, Forge Learn, and the newer Forge Builder work behind one local Forge Core while preserving each app's distinct workflow and identity.

The individual portfolio folders below remain useful project history and demonstrations. Where they differ, **`forge-suite/current/` is the controlling current local implementation**.
<!-- FORGE-SUITE-PORTFOLIO:END -->

## Applications

### Forge Builder
**Public standalone repo:** https://github.com/ajkivela369-coder/forge-builder

A local-first prompt-to-app workspace with replaceable model/provider adapters, sandboxed project generation, editable source, local preview, Git snapshots, QA gates, and explicitly authorized deployment paths. The integrated Forge development line now also includes provider-neutral routing, project sandboxing, snapshot endpoints, static validation, and real browser smoke checks.

### [SearchSignal — SEO + GEO Operations Lab](searchsignal/)
**Live:** https://forgesearcher.floot.app/

A working higher-education web-operations portfolio app with a secure server-side public-URL crawler, explainable SEO/GEO scoring, content-optimization drafts, schema.org JSON-LD tooling, roadmap prioritization, analytics/CSV workflows, WordPress-support scenarios, training modules, and a technical lab. Working features, connector-ready integrations, and learning-only surfaces are explicitly separated.

### [AJ Job Fisher](aj-job-fisher/)
**Live:** https://aj-job-fisher-a2507o.v2.appdeploy.ai/

A job-search control center with weighted fit scoring, duplicate detection, guardrails for remote/pay/travel/credentials, job-URL ingestion, application-package preparation, queue/evidence tracking, and explicit stop conditions for questions or commitments that require human review.


### [NeuroEval](handshake-neuroeval/)
Biology and neuroscience response evaluation with transparent scoring for concept coverage, mechanistic reasoning, uncertainty calibration, evidence language, clarity, and unsupported certainty.

### [HealthQA Auditor](meridial-healthqa/)
Safety-first health-science AI output auditing with PASS / REVIEW / ESCALATE dispositions, patient-specific claim detection, dosing-language flags, urgent-symptom escalation checks, and machine-readable reviewer output.

### [Evidence Auditor Pro](evidence-auditor/)
Privacy-safe benefits/disability evidence intelligence with source/page provenance, quote-integrity checks, issue mapping, favorable/unfavorable/mixed/neutral classification, missing-record signals, contradiction pairing, evidence matrices, packet generation, and Elias, a citation-first evidence assistant. Synthetic or de-identified examples only.

### [PairRank](pairrank/)
Pairwise LLM-response evaluation with weighted rubrics, A/B preference labels, failure tags, reviewer notes, written justification, and JSON export.

### [CiteGuard](citeguard/)
Scientific claim-to-source auditing with claim/source mapping, lexical-support triage, overclaim detection, weak-support routing, and structured audit export. It explicitly distinguishes source matching from truth verification.

### [RaterLab](raterlab/)
Annotation quality assurance and reviewer calibration with gold-set accuracy, inter-rater agreement, Cohen's kappa, disagreement queues, label-distribution inspection, and calibration exports.

### [Benchmark Forge](benchmark-forge/)
Structured AI benchmark authoring for prompts, expected concepts, prohibited misconceptions, difficulty, gold labels, reviewer rationales, coverage reporting, and JSON/JSONL export.

### [GrimForge Studio — App XIII](grimforge-studio/)
A cinematic lore-production studio for original grimdark science-fiction commentary and old-world dark-fantasy storytelling. It combines a Reference DNA Lab, thesis-first Lore Scholar, Channel Forge, narrator direction, cinematic Director Timeline, controlled humor, source/canon labeling, Rights Guard, and production-package export. Reference creators inform only high-level production attributes; the app does not copy scripts, artwork, jokes, or voice identities.

### [StudyForge](studyforge/)
An adaptive MLT/ABOR study coach with source-grounded study-pack generation, Exam Coach scoring, weak-area remediation, a Reference Lab that learns accessible high-level teaching patterns from public channels/sites, curated education-channel presets, and the floating Forge Tutor copilot.

### [WildTake Studio](wildtake-studio/)
A rights-aware short-form wildlife/animal commentary studio with timed action beats, original AI commentary packs, a weighted Reference Lab for public channels/sites, curated production presets, and the floating Wild Copilot. Reference sources shape abstract pacing, hooks, structure, humor density, and educational framing—not scripts, voices, catchphrases, artwork, or creator identity.

### [CareFlow Research Lab](careflow-research-lab/)
An independent healthcare UX research portfolio study built around a fictional medication-coordination workflow. It demonstrates research planning, interview/contextual-inquiry frameworks, moderated usability testing, task/confidence metrics, structured observation capture, affinity synthesis, evidence traceability, findings prioritization, research-repository design, and responsible AI-assisted synthesis. Seeded study data are explicitly simulated; the project does not claim BetterRX employment, client work, real participants, or real-world outcome metrics.

## Design principles

- Transparent, inspectable baselines rather than hidden claims of model intelligence.
- Human review remains explicit in every high-stakes workflow.
- Machine-readable outputs support reproducible evaluation and QA.
- Portfolio examples use synthetic or de-identified data where privacy matters.
- Creative tools distinguish inspiration from imitation and track asset rights before publication.
- Projects are demonstrations of hands-on AI-evaluation and production work, not claims of paid AI employment or production clinical/legal systems.

## Portfolio quality control

Every cataloged project is covered by a reusable GitHub Actions quality gate in [Portfolio QC](../.github/workflows/portfolio-qc.yml). The full rubric and current verification matrix are documented in [Portfolio Quality Control](QUALITY_CONTROL.md). The gate inventories app/source paths, checks README encoding and provenance, parses manifests, compiles Python, runs evaluator tests, builds the Vite portfolio apps, and smoke-tests all listed public deployments.

A passing static/fixture gate does **not** convert unverified live-engine, clinical, media-quality, or user-research claims into verified results. Those remain labeled separately and require the relevant real-world acceptance work.

## Direction

The portfolio is being built as a coherent lab rather than a collection of unrelated demos. Future apps and upgrades can extend into prompt-adversarial testing, multimodal/document-output QA, model regression testing, evaluation analytics, workflow-quality review, voice/video production, and creator tooling.
