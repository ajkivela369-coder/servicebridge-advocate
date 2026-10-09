# AJ AI Evaluation Lab

A growing collection of compact, auditable AI applications spanning neuroscience, health-science safety, evidence review, pairwise preference evaluation, citation QA, annotation calibration, benchmark authoring, and creative media production.

## Current Forge-managed live portfolio — October 9, 2026

[Open all seven demos](https://aj-forge-portfolio.vercel.app/#projects). Forge is the primary deployment workflow; public HTTPS uses its existing Vercel adapter. SearchSignal has a published [Floot backup](https://forgesearcher.floot.app/). The other six demos currently use Forge.

| App | Current live demo |
|---|---|
| Evidence Auditor | [Open](https://aj-forge-portfolio.vercel.app/apps/evidence/) |
| SearchSignal | [Open](https://aj-forge-portfolio.vercel.app/apps/searchsignal/) |
| NeuroEval | [Open](https://aj-forge-portfolio.vercel.app/apps/neuroeval/) |
| HealthQA Auditor | [Open](https://aj-forge-portfolio.vercel.app/apps/healthqa/) |
| PairRank | [Open](https://aj-forge-portfolio.vercel.app/apps/pairrank/) |
| CiteGuard | [Open](https://aj-forge-portfolio.vercel.app/apps/citeguard/) |
| GrimForge War Theater | [Open](https://aj-forge-portfolio.vercel.app/apps/grimforge/) |

The public evidence workflow handles browser-side document review and reviewed PDF/ZIP exports. Evaluation tools expose deterministic scoring or human judgments. GrimForge's public demo generates a playable storyboard and planning exports; full local rendering remains a separate Forge workflow. Preserved standalone sources and earlier build records below describe their own versions.

## Guided Forge browser apps - October 9, 2026

The four public evaluation apps now explain their purpose, who should use them, and each step from sample inputs to a reviewed report. Start in Simple mode; Pro adds inspectable output and controls.

| App | Use it for | Live app |
|---|---|---|
| NeuroEval | Review an explanation against expected concepts across eight neuroscience topics or your own topic | [Open NeuroEval](https://aj-forge-portfolio.vercel.app/apps/neuroeval/) |
| HealthQA Auditor | Inspect configured health-content warning patterns and record human review | [Open HealthQA](https://aj-forge-portfolio.vercel.app/apps/healthqa/) |
| PairRank | Rate two answers with a shared rubric and explain your preference | [Open PairRank](https://aj-forge-portfolio.vercel.app/apps/pairrank/) |
| CiteGuard | Find source-match candidates, then record whether the source actually supports each claim | [Open CiteGuard](https://aj-forge-portfolio.vercel.app/apps/citeguard/) |

[Current shared source and usage guide](ai-evaluation-lab/) - [Upgrade record](ai-evaluation-lab/BUILD_AND_UPGRADE.md) - [Verification](ai-evaluation-lab/VERIFICATION.md). Earlier Python projects below remain available as project history.

<!-- FORGE-SUITE-PORTFOLIO:START -->
## Current integrated Forge Suite

The integrated Forge line is now synchronized through **Forge Learn v0.5.9**. It connects Forge Workspace, Elias, Evidence Auditor, MedForge, GrimForge, Forge Learn, Forge Builder, and the current VocalForge MVP to a shared evidence-first build/learning story while preserving each app's distinct workflow and maturity boundary.

The individual portfolio folders below remain useful project history and demonstrations. Where they differ, **`forge-suite/current/` is the controlling current local implementation**.
<!-- FORGE-SUITE-PORTFOLIO:END -->

## Featured Forge websites and plugins — October 6, 2026

| Product | Companion website | ChatGPT plugin | Purpose |
|---|---|---|---|
| Grim Forge Commander V2 | [Website](https://grim-forge-commander.ajkivela369.chatgpt.site) | Existing private V2 installation | Private laptop orchestration for Forge, Blender, FFmpeg, Git, and project automation. |
| GrimForge Cinema | [Website](https://grimforge-cinema.ajkivela369.chatgpt.site) | [Private plugin](https://chatgpt.com/plugins/plugins_6ac49641fa9c8191b0d87ee45606b7fd) | Original cinematic planning, continuity, local production readiness, rendering, narration, captions, and review. |
| Elias | [Website](https://elias.ajkivela369.chatgpt.site) | [Private plugin](https://chatgpt.com/plugins/plugins_6ac49646640c8191b3114777a696751a) | General assistance, document questions, source-grounded reasoning, and clear next steps. |
| Evidence Auditor | [Website](https://evidence-auditor.ajkivela369.chatgpt.site) | [Private plugin](https://chatgpt.com/plugins/plugins_6ac4964b0e248191b1bc2d7cc172a96c) | Source/page provenance, chronology, support, tensions, missing evidence, and reviewed packets. |

The four companion websites are deployed with an owner-only audience at this snapshot. Their metadata, branded thumbnails, canonical URLs, structured data, robots files, and sitemaps are prepared for public sharing; private pages are not claimed to be publicly indexed. The three new app plugins are private workflow packages using the existing Grim Forge Commander connection. They do not expose a separate public app backend or an app-scoped security boundary.

Local Elias is a general assistant. The hosted Elias evidence demo includes Evidence Auditor as its specialist workspace; the separate websites and plugins explain those roles without claiming identical local and hosted builds.

[Association directory](COMPANION_SITES.md) · [Private plugin source](plugins/) · [Public readiness](PUBLIC_READINESS.md)

## Applications

### [Grim Forge Commander V2](grim-forge-commander/)
Private laptop orchestration for Forge, Blender, FFmpeg, Git, and project automation. Server 2.0.0 registers 46 tools; the current ChatGPT connection retains 10 native tools. The branded 1.0.1 plugin package and its companion website are separate from the server upgrade archive. See its [build history](grim-forge-commander/BUILD_AND_UPGRADE.md).

### [SearchSignal — SEO + GEO Operations Lab](searchsignal/)
**Current standalone source:** [searchsignal/interview-build/](searchsignal/interview-build/)

**Current Forge-managed employer-neutral demo:** https://aj-forge-portfolio.vercel.app/apps/searchsignal/

**Published Floot backup:** https://forgesearcher.floot.app/

An employer- and industry-neutral web-operations portfolio app with secure public-URL auditing, bounded same-site crawling, Change Lab verification, recurring site-pattern analysis, linked-document intelligence, redirect-chain validation, explainable SEO/GEO scoring, content/schema tooling, editable prioritization, reporting, analytics CSV workflows, CMS support/training, explicit technical-escalation boundaries, and synthetic 20K-page / 15K-document scale simulation. The case-study workflow uses public evidence and clearly labeled demo inputs rather than employer-specific assumptions.

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

### [VocalForge](vocalforge/)
A local-first vocal recording, analysis, enhancement, comparison, and export workstation. The current MVP preserves original takes, exposes an inspectable processing chain, supports Natural / Pure, Studio Vocal, and Comfort Mode concepts, and keeps later-phase audio features explicitly separate from verified current behavior.

### [CareFlow Research Lab](careflow-research-lab/)
An independent healthcare UX research portfolio study built around a fictional medication-coordination workflow. It demonstrates research planning, interview/contextual-inquiry frameworks, moderated usability testing, task/confidence metrics, structured observation capture, affinity synthesis, evidence traceability, findings prioritization, research-repository design, and responsible AI-assisted synthesis. Seeded study data are explicitly simulated; the project does not claim BetterRX employment, client work, real participants, or real-world outcome metrics.

## Build + upgrade histories

The portfolio now keeps a step-by-step build and upgrade record for every cataloged app. Start with [BUILD + UPGRADE INDEX](BUILD_AND_UPGRADE_INDEX.md). The employer-facing presentation layer has its own [website build + upgrade history](WEBSITE_BUILD_AND_UPGRADE.md). Each app history separates implementation, automated verification, live deployment evidence, and target-PC or human-research acceptance.

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

## Archived applications

- **AJ Job Fisher** - retired October 5, 2026 after portfolio QA. Source and build history remain preserved in [`aj-job-fisher/`](aj-job-fisher/), but it is no longer an active portfolio app or live-demo claim.
