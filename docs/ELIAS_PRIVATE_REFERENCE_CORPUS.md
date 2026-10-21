# Elias Private Reference Corpus

Status: active development policy.

The user has authorized prior packets, prior ChatGPT work, relevant connected-drive materials, and
current uploads to be used as private reference material for Elias development.

## Purpose

The corpus is intended to make Elias better at:
- veteran-facing evidence packet architecture;
- reviewer navigation and visual hierarchy;
- evidence/source control;
- point-by-point rebuttal design;
- issue matrices and chronology;
- tool-routing and planner evaluation;
- retrieval edge cases;
- failure-mode discovery;
- packet QA.

## Four data tiers

### 1. Private reference
May contain real personal/case information. Can inform pattern extraction and evaluation design.
Must not be committed to the public repository.

### 2. Reviewed gold
De-identified cases whose labels, relevance links, expected routes, and source relationships have
been manually checked. May be used for fixed evaluation.

### 3. Synthetic public
Fully synthetic public examples for CI, demos, documentation, and teaching.

### 4. Production case
Live case data used for the user's active workflow. It is not automatically converted into a public
example or benchmark.

## Derivation rule

Private sources do not need to become public source files for Elias to learn from the work.

Preferred path:

```text
private packet / chat / connected-drive file
                  ↓
        extract reusable pattern
                  ↓
       remove identifiers / case facts
                  ↓
   separate record fact from advocacy pattern
                  ↓
             human review
                  ↓
     synthetic or de-identified case
                  ↓
      fixed benchmark expectation
                  ↓
            public CI test
```

## Public-repository prohibition

Do not commit raw private medical records, military records, benefit records, emails, claim numbers,
personal identifiers, connected-drive IDs, screenshots containing PII, or private source indexes.

## Packet-specific learning

Private packet families may teach Elias:
- cover/read-first conventions;
- evidence-roadmap/index structure;
- issue-by-issue advocacy;
- source screenshot placement;
- evidence-card design;
- exact-quote/source-page verification;
- chronology presentation;
- favorable/adverse evidence reconciliation;
- mechanism-exhibit labeling;
- requested-action framing;
- filing-size and version conventions.

The model should learn the **structure and method**, not publish the underlying private case.
