# Elias Orchestration Architecture — Candidate Design

Status: **Build Lab prototype / production candidate**

This document defines a candidate orchestration layer for Elias. It does not claim that autonomous
agent routing is deployed in production.

## Goal

Turn Elias from a collection of adjacent capabilities into one evidence agent that can decompose a
user goal, select the appropriate intelligence/tool for each subtask, preserve provenance, and stop
for human approval before consequential actions.

## Core pattern

```text
User goal
   ↓
Planner
   ↓
Model router ───── Tool registry
   ↓                    ↓
deterministic      evidence/search tools
local model        provenance tools
frontier LLM       packet/verification tools
   └───────────────┬────┘
                   ↓
              plan state
                   ↓
           verification layer
                   ↓
             human approval
                   ↓
                output
```

## Routing principle

Use the least complex component that can reliably solve the subtask.

- Exact phrases, dates, source locators, deterministic packet assembly → ordinary code.
- Semantic retrieval / narrow classification → specialized local models where benchmarked.
- Complex comparison, explanation, synthesis, drafting → frontier LLM.
- Important generated propositions → reconnect to Claim → Source Trace.
- Consequential write/export actions → explicit user approval.

## Production promotion gates

Before this architecture moves into Elias:
1. define task classes and expected routes;
2. create planner regression cases;
3. benchmark routing accuracy;
4. log tool inputs/outputs and plan state;
5. preserve source IDs and locators across tool calls;
6. add retry/failure states that do not silently continue;
7. require approval for packet write/export and similar state-changing actions;
8. measure latency and model/API cost;
9. test adversarial or ambiguous requests;
10. validate that the router does not bypass evidence-verification rules.

## Initial tool registry

- evidence.search_lexical
- evidence.search_semantic
- evidence.trace_claim
- evidence.find_contradictions
- evidence.build_timeline
- evidence.verify_quote
- authority.verify
- reason.synthesize
- packet.build
- packet.qa

## Important boundary

The planner decides **what to do next**. It does not decide what is factually true. Source evidence,
verification state, and human review remain authoritative.


## Veteran advocacy autonomy

For veteran-benefits packet work, the desired production behavior is **bounded advocacy autonomy**.

Elias may autonomously:
1. search and re-search the case record;
2. build an issue matrix for each contested issue;
3. audit an adverse VBA decision against the source record;
4. identify favorable evidence, adverse evidence, missing evidence, and unresolved conflicts;
5. verify configured official authority;
6. build rebuttal maps;
7. draft, reorganize, and revise packet sections;
8. rerun packet QA and citation checks until the internal draft is ready.

The approval boundary should be the final export / filing handoff, not each internal analysis or
draft revision.

The planner must stop rather than comply when asked to fabricate evidence, preserve an unverified
quote as exact, invent missing dates, delete or hide adverse evidence, or state a medical conclusion
that exceeds the source record.

The advocacy objective is asymmetric in purpose but constrained by evidence: Elias is allowed to
work toward the veteran's strongest supportable case. It should not artificially balance the
veteran's position with the agency's position, but it must accurately surface and address material
contrary evidence because hiding it would weaken both reliability and advocacy.
