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
| Submission builder | **Expanded in the GitHub development snapshot.** Packet Studio can now select derived page captures/illustrations from a private visual library and compose them as dedicated, provenance-labeled pages in the exact filing PDF. |
| Provenance | **Materially expanded:** Claim → Source Trace resolves filenames/locators and verifies literal quotes; derived page captures and illustrations store provenance metadata; visual PDF pages carry derived-visual warnings. A reusable saved claim graph with manual approval state remains a next step. |
| Human verification | Established product rule and visible gate |
| Visual packet composer | **Implemented in the GitHub development snapshot.** Approved derived visuals can be selected in Packet Studio, optimized as packet-only copies, and inserted into dedicated polished PDF pages with provenance captions. |
| Screenshot/page selection | **Partial in the GitHub development snapshot.** Source Page Lab can open retained PDF originals, render a chosen page, auto-trim outer whitespace, stamp source filename/page, and save a separately labeled derived capture. Automatic relevance-based page/region selection still needs development. |
| Screenshot cropping + source/page labels | **Partial.** Automatic outer-whitespace trimming plus source/page stamping is implemented for retained PDF pages. Clinically relevant sub-region selection/cropping remains a next step. |
| Injury illustrations tied to records | **Implemented in the GitHub development snapshot as Illustration Lab.** It builds a de-identified brief from selected sources, generates an educational illustration, saves provenance metadata with the source IDs/locators, and labels the result as an illustration rather than medical imaging or diagnostic proof. |
| CFR/state authority verification | **Live verification added for configured program/issue authority pages.** Evidence Auditor records reachability, title, authority category, and check time for VA/VBA, SSA, New Hampshire, and medical-function mappings. This verifies configured source availability/category—not legal sufficiency or dispositive applicability. |
| Under-5-MB final submission | **Validation + packet-only reduction implemented in the GitHub development snapshot.** Simple Mode measures the exact combined PDF byte size and PDF.js verifies page rendering. Selected visuals are optimized for the packet, and if the first combined PDF exceeds 5 MB Elias retries with smaller packet-only image copies while preserving stored assets. The app still reports OVER 5 MB if the final exact file remains above the limit; success is never assumed. |
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
7. Expand the implemented Source Page Lab from page-level auto-trim/stamping into relevance-based page and sub-region selection.
8. Expand the implemented Illustration Lab with reusable visual templates and manual edit/approval; direct Packet Studio handoff is now implemented through the Derived Visual Library.
9. Expand the implemented visual packet compositor with drag/reorder, per-visual captions, and bundle-scoped default visual selection.
10. Strengthen the implemented packet-only visual reduction with additional PDF-level optimization strategies for rare files that remain over the configured submission limit.
11. Verify storage/auth/security architecture before any HIPAA/compliance marketing language.

## Product language

Preferred positioning:

> **Elias** — patient-controlled evidence intelligence.
>
> **Evidence Auditor** — prove it, source it, package it.

The product should never imply that AI replaces the medical record, the clinician, the adjudicator, or legal review.
