# SearchSignal — SEO + GEO Operations Lab

**Live app:** https://forgesearcher.floot.app/

SearchSignal is an independent portfolio project demonstrating higher-education web operations across traditional SEO, generative/AI engine optimization (GEO), structured data, content optimization, analytics workflows, WordPress support, training, and technical change boundaries.

## What is working

- Server-side public-URL auditing with URL validation, private-network blocking, redirect checks, timeouts, HTML content-type validation, and response-size limits.
- Explainable SEO and GEO scoring with per-check evidence, rationale, and point contributions.
- Inspection of title, meta description, canonical, robots directives, language, heading structure, word count, links, image-alt coverage, JSON-LD/schema types, and common WordPress fingerprints.
- Rule-based content optimization drafts and AI-answer-readiness preview.
- JSON-LD generation for WebPage, Article, Course, and FAQPage.
- Now / Next / Later prioritization workflow.
- CSV-based analytics import demonstration and a manual AI-visibility evidence log.

## Connector-ready / learning surfaces

Google Search Console, Google Analytics, self-hosted WordPress, and WordPress.com are shown as connector-ready only. They are **not presented as authenticated production integrations** in the public demo.

The independent local Apache/PHP/MariaDB Multisite lab passed 24 automated checks, followed by browser verification of departmental navigation and authenticated Network Admin. The separate Playground Blueprint also launched successfully. See [lab acceptance](wordpress-lab/ACCEPTANCE.md). This is hands-on training evidence, not production administration employment.

## Source snapshot

The `source/` directory contains an earlier six-file Floot implementation snapshot. Current v2 parity is blocked pending source access; see [V2 synchronization status](V2_SYNC_STATUS.md):

- `source/pages/_index.tsx` — application UI and portfolio workflows
- `source/pages/_index.module.css` — responsive interface styling
- `source/endpoints/audit_POST.ts` — secure server-side crawler and scoring logic
- `source/endpoints/audit_POST.schema.ts` — typed endpoint contract
- `source/base.css` — visual tokens
- `source/design-principles.md` — design rationale

Floot supplies shared UI primitives and hosting/runtime infrastructure, so this snapshot is intended for code review rather than as a standalone clone.

## Quality status

On 2026-09-30, the production homepage returned HTTP 200, the deployed assets loaded, and the production audit endpoint successfully returned both SEO and GEO scores for a public test page. The auditor also rejects local/private-network targets.

See [Portfolio Quality Control](../QUALITY_CONTROL.md) for the shared QC contract and automation.

## Build + upgrade history

See [BUILD_AND_UPGRADE.md](BUILD_AND_UPGRADE.md) for the step-by-step implementation and upgrade trail, including what is verified live versus connector-ready.

## Provenance

Independent portfolio demonstration by AJ Kivela. Not affiliated with or endorsed by Dartmouth College or the Geisel School of Medicine. Demo/sample metrics are labeled as such, and unconnected integrations are not represented as live.