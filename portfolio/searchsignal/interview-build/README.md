# SearchSignal — SEO + GEO Operations Lab

**© 2026 Alexander J. Kivela. Proprietary software. All rights reserved.** See the repository `LICENSE`.

SearchSignal is an independent, employer- and industry-neutral portfolio application for evaluating public websites and turning SEO, GEO/AI-readiness, structured data, content quality, analytics evidence, CMS support, training, and web-governance findings into an accountable operating workflow.

## Working in the demo
- **Case Studies**: a guided public-data workflow connecting audit evidence → prioritization → safe implementation/support → measurement, with explicit accuracy boundaries.
- Editable prioritization using organizational impact, visibility gap, competitive pressure, demand/capacity pressure, team capacity, and implementation effort; sample inputs are clearly labeled illustrative.
- Server-side public URL auditing with private-network blocking, redirect checks, timeouts, HTML-only validation, and bounded response size.
- Site Intelligence with bounded same-origin crawling, page inventory, linked PDF/Office document discovery/checks, architecture summaries, JSON evidence export, and redirect-chain validation.
- Site Patterns for recurring title, canonical, heading, and linked-document signals from bounded crawl evidence.
- Document Intelligence for status, size, Last-Modified, duplicate filenames, weak link text, and referencing-page signals.
- Explainable SEO/GEO scoring with evidence-linked findings and proprietary weighting retained server-side.
- Change Lab for synthetic find → fix → verify workflows without modifying production sites.
- Structured-data and content optimization tools.
- Interactive CMS support/training workflows with explicit escalation boundaries.
- Browser-local Search Console / Analytics CSV summaries and 7/30/90-day comparison workflows; no fake authenticated connection.
- Progress & Reporting with owner-aware roadmap tracking and JSON/CSV/print-to-PDF outputs.
- 20K / 15K synthetic scale simulation for batching, rate limits, caching, checkpoints, pause/resume, and prioritization without crawling external sites.
- Capabilities Coverage separating implementation, automated-test coverage, and live verification.
- Repeatable QA for syntax, health, case-study workflow, private-network protection, public auditing, site scanning, redirects, implementation workflows, and security boundaries.

## Product review path
Use [CASE_STUDY_WALKTHROUGH.md](CASE_STUDY_WALKTHROUGH.md) for a concise review path and [BUILD_AND_UPGRADE.md](BUILD_AND_UPGRADE.md) for the implementation trail.

Run `npm run qa` to execute the local quality gate. See the public mirror's [licensing and IP boundary](../LICENSE_BOUNDARY.md) for the source-history boundary.

## Connector-ready, not represented as live
- Google Search Console
- Google Analytics
- Self-hosted WordPress
- WordPress.com

## Learning lab, not represented as production administration
- Apache and .htaccess concepts
- PHP / WordPress template safety
- MariaDB/MySQL application concepts

## Accuracy boundary
SearchSignal analyzes public pages and uses clearly labeled demo data where live account connections are not present. Analysis of a public site does not imply affiliation, internal credentials, analytics access, production administration, or authorization to publish changes.
