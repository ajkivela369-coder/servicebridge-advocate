# Elias + Evidence Auditor v9 — Evidence Cloud Roadmap

This document is intentionally de-identified. It defines product boundaries and implementation targets; it is not a representation that every target is already deployed.

## Product decision

**Elias is the master application shell. Evidence Auditor is the second flagship capability inside the same product.**

Evidence Auditor may also receive its own public landing page/route later, but it should not create a separate patient-data silo. The shared case layer remains the Evidence Cloud.

## Unified specialist model

| Specialist | Job |
| --- | --- |
| Elias | Orchestrate the full case and route work |
| Evidence Auditor | Audit support, contradictions, gaps, chronology, provenance and reviewer-readiness |
| NeuroEval | Review neurologic and functional evidence without inventing diagnosis/causation |
| HealthQA | Explain supplied medical evidence in patient-friendly language |
| Packet Builder | Assemble verified evidence into structured draft submissions |
| Citation Auditor | Verify that important statements trace to actual sources |
| Document Copilot | Organize and format evidence-backed pages and sections |

All specialists use the same user-scoped case record and the same evidence-type boundaries.

## Evidence Cloud capability status

| Capability | v9 status / rule |
| --- | --- |
| Shared source library | Implemented conceptually in the existing persistent case workspace; surfaced as Evidence Cloud in the public UI snapshot |
| PDF/text/image/email intake | Existing implementation supports these paths; media review also exists |
| Large searchable PDF indexing | Existing implementation |
| OCR image intake | Existing implementation |
| Automatic evidence grouping | Added as a transparent filename/excerpt heuristic in the public UI snapshot; deeper metadata classification still needs backend work |
| Smart metadata extraction | Partial; source/page/date metadata exists in places, but provider/facility/document-type extraction is not complete end-to-end |
| Patient timeline | **Persistent normalized Evidence Timeline implemented in the GitHub development snapshot.** Generated events must resolve to indexed source filenames; uncertain dates stay explicit and a human-verification warning is retained. |
| Statement-to-source linking | **Structured Claim → Source Trace implemented in the GitHub development snapshot.** It resolves filenames to indexed sources, attaches stored locators, separates support/conflict/context, and only preserves an exact quote when literal source-text verification succeeds. |
| Persistent reference across specialists | Product architecture established; specialists are unified behind the same Copilot and case record |
| Duplicate/version control | **Advisory detection implemented in the GitHub development snapshot** using deterministic content fingerprints and filename-normalized possible-version groups. No automatic deletion/overwrite; human verification remains required. |
| Natural-language case search | Existing record search/chat supports evidence queries; dedicated vault search is now surfaced locally in the snapshot |
| Evidence bundles | **Implemented in the GitHub development snapshot** as user-scoped saved collections of source IDs. Bundles do not duplicate or rewrite underlying evidence. |
| Submission builder | Existing Packet Studio / filing workflow |
| Provenance | Existing rules and citations; structured provenance graph remains a next step |
| Human verification | Established product rule and visible gate |
| Screenshot/page selection | Needs development |
| Screenshot cropping + source/page labels | Needs development |
| Injury illustrations tied to records | Needs development; must distinguish illustration from source evidence |
| CFR/state authority verification | Partially supported for configured official-reference flows; must remain date/program specific |
| Under-5-MB final submission | Partial only; packet generation exists, but automated page selection, visual QA, and reliable final compression are not yet guaranteed |
| Immutable original evidence storage | Required architecture target; do not claim verified immutability until deployed storage/versioning is confirmed |
| Encryption/access/audit controls | Must be verified against the actual hosting/storage implementation before making security or compliance claims |
| HIPAA compliance | Do not claim unless the deployed infrastructure, contracts/BAA, data flows, and operational controls are actually verified |

## Evidence Trace

Every important generated proposition should be able to expose:

**Source → page/locator → extracted evidence → evidence classification → interpretation → generated statement**

Evidence classifications include:

- exact quote
- paraphrase
- claimant-reported history
- clinician observation
- objective test
- medical opinion
- agency finding
- AI/analyst synthesis

A broken or ambiguous link should become an audit warning rather than being silently repaired by the model.

## Floating Copilot behavior

The Copilot remains available across the app and can switch specialist modes without changing the underlying case.

Primary verbs:

**Find → Compare → Explain → Organize → Link → Draft → Build → Verify → Export**

The desired direction is app-operating behavior: filter evidence, select sources, build a chronology, create a bundle, populate a packet, flag contradictions, or prepare export. The user should be able to see and review those changes.

## Next implementation sequence

1. Create a structured EvidenceItem + SourceLocator + EvidenceClaim data model.
2. Add backend metadata extraction and confidence/verification state.
3. Strengthen current advisory duplicate/version detection with cryptographic file hashes for stored originals and explicit human-confirmed version relationships.
4. Expand the now-persistent Evidence Timeline with manual correction/approval states, stable event IDs, and bundle-scoped chronology.
5. Expand the now-implemented Evidence Bundles with rename/edit, bundle-scoped audit, and packet handoff.
6. Expand the implemented Claim → Source Trace into a reusable claim graph with saved claim nodes, manual approval states, and packet-level Citation Auditor blockers.
7. Add page-image extraction, crop selection, and source/page stamping.
8. Add diagram/illustration generation with explicit "illustration, not source evidence" labeling.
9. Add packet compositor that preserves selected source visuals.
10. Add automated visual QA and final under-5-MB compression verification.
11. Verify storage/auth/security architecture before any HIPAA/compliance marketing language.

## Product language

Preferred positioning:

> **Elias** — patient-controlled evidence intelligence.
>
> **Evidence Auditor** — prove it, source it, package it.

The product should never imply that AI replaces the medical record, the clinician, the adjudicator, or legal review.
