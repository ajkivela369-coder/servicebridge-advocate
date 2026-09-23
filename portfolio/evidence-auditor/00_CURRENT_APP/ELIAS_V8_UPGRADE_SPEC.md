# Elias Evidence Playbook v8 — Agency-Aware Filing Engine

This public specification is deliberately de-identified. It contains generalized evidence-review behavior only. No private claimant records, names, identifiers, diagnoses, case facts, or source text belong in this repository.

## Source-control rules

1. Original source records control over summaries, captions, generated prose, diagrams, and advocacy synthesis.
2. Keep evidence types distinct: exact quotation, paraphrase, claimant-reported history, clinician observation, objective testing, medical opinion, agency finding, and analyst synthesis.
3. Never promote one evidence type into another. Similar wording is not an exact quote; a claimant report is not an objective finding; AI synthesis is not a clinician opinion.
4. Prefer pinpoint source locators and stable source identities. Broad file-chunk references are a review cue, not a strong locator.

## Agency-aware filing architecture

### VA / VBA

Build a date-specific duty-status chronology before nexus or aggravation analysis when Guard, Reserve, ROTC/SMP, ACDUTRA, INACDUTRA, or Title 32 status is material. Address direct service connection, qualifying-duty injury/aggravation, secondary causation, and secondary aggravation separately when raised. Missing LOD records or incomplete diagnostic workup are development gaps unless an actual adverse finding establishes something more. Reconcile favorable opinions explicitly before relying on a contrary opinion. Analyze frequency, duration, unpredictability, recovery, attendance, pace, persistence, safety, and reliability when supported by the record.

### Social Security SSDI / SSI

Do not recycle service-connection framing. Organize the filing around the five-step disability framework, medically determinable impairments, severity and duration, Listings when raised, symptom evaluation, medical opinions and prior administrative findings, RFC by function, past relevant work, other-work analysis, and the ability to sustain attendance, pace, persistence, breaks, and reliability over a regular work schedule.

### State disability / benefits

Use the actual state statute, regulation, or program rule. Import a federal standard only when the state authority actually incorporates it. Keep state-specific eligibility elements separate from federal disability analysis.

## Submission preflight

A filing must not receive a Ready to Submit status when any blocking condition exists, including:

- no verified governing authority;
- a requested issue has no issue-specific argument;
- a material proposition has no claimant-record citation;
- source identity is ambiguous enough to prevent meaningful verification.

The system should downgrade to Needs Review when non-blocking quality problems remain, including:

- broad or weak source locators;
- duplicated source identities;
- an appendix dominated by uncited material;
- weakly matched medical literature.

## Source appendix

The filing appendix should normally contain the high-yield sources actually cited in the brief. Deduplicate by stable source identity. Give each source a meaningful use label and a useful locator. The internal neutral audit may retain a fuller inventory.

## Medical literature

External research queries must be de-identified and derived from the public program/issue or medical mechanism being researched. Do not send claimant names, diagnoses copied from the record, dates of birth, claim numbers, quotations, or private source text to a general literature/web search. Include only strongly matched verified literature; zero relevant papers is better than padded tangential citations.

## Recommended filing sequence

Requested Action / What Matters Now → Issues Presented → agency-specific chronology/framework → objective findings → favorable evidence map → record-grounded medical and legal arguments → functional reliability/RFC or work-impact analysis → governing authorities → tightly relevant literature → focused development questions when appropriate → concise cited-source appendix → Requested Disposition.

The internal audit remains separate and may include weaknesses, conflicts, gaps, and adverse evidence. The claimant-facing advocacy filing may prioritize favorable supportable evidence but must not fabricate, misquote, or omit context necessary to keep a proposition accurate.


## Unified flagship architecture — v9 direction

Elias and Evidence Auditor are not separate evidence silos.

- **Elias** is the master case orchestrator and user-facing assistant.
- **Evidence Auditor** is the flagship audit workspace for support, contradictions, gaps, provenance, chronology, functional reliability, and reviewer-readiness.
- **Evidence Cloud** is the shared patient-controlled source layer.
- **NeuroEval** is a specialist neurologic/functional evidence reviewer.
- **HealthQA** is a patient-friendly health-record explanation mode that must not invent diagnosis or causation.
- **Packet Builder** assembles verified evidence into structured draft submissions.
- **Citation Auditor** checks whether important propositions actually trace back to the record.
- **Document Copilot** organizes and formats evidence-backed sections and pages.

The user should not have to upload the same record separately to each specialist. Every specialist should operate against the same user-scoped case evidence and preserve the same evidence-type boundaries.

## Patient Evidence Cloud target

The Evidence Cloud is more than a file uploader. The target capability set is:

1. patient-controlled upload of PDFs, images, video, audio, letters, forms, screenshots, email exports, and other supported evidence;
2. automatic evidence grouping without changing the original source;
3. metadata extraction for provider/facility, record date, document type, page count, issue, source, and upload time when supportable;
4. chronology/timeline generation with source locators;
5. statement-to-source links;
6. persistent reference across Elias and every specialist mode;
7. duplicate and version detection that never destroys the original record;
8. natural-language case search;
9. evidence bundles for VA, SSA, state disability, ADA, clinician review, attorney review, and other case-specific workflows;
10. packet assembly using selected source pages and visuals;
11. provenance for generated outputs;
12. explicit uncertainty flags and human verification gates.

## Copilot operating model

The floating Copilot should be able to **operate on the app**, not only answer questions.

Primary verbs:

`Find → Compare → Explain → Organize → Link → Draft → Build → Verify → Export`

Actions that change case organization, selected evidence, or packet composition should remain visible and reviewable. Consequential submission/export actions should preserve a human approval step.

## Original-source protection

The intended architecture treats original evidence as source-of-truth material and stores AI-created summaries, labels, relationships, diagrams, interpretations, and draft prose separately.

The public repository must not claim that immutable object/version storage is fully enforced unless the deployed storage implementation is verified to do so. Until then, **original-source control is a required architecture rule, not a compliance claim**.

## Automated polished-page pipeline target

The target pipeline is:

`Patient files → evidence graph → relevant-page selection → screenshot/crop → source label → narrative → diagram → citations → packet → visual QA → compression`

Screenshot/crop selection, injury illustration generation, final visual QA, and reliable under-5-MB compression are not complete merely because ordinary packet generation exists. The UI and documentation must keep that distinction visible.
