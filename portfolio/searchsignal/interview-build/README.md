# SearchSignal — SEO + GEO Operations Lab

**© 2026 Alexander J. Kivela. Proprietary software. All rights reserved.** See the repository `LICENSE`.

Independent portfolio application demonstrating a workflow for technical SEO, generative/AI engine optimization (GEO), structured data, web-program prioritization, analytics reporting, WordPress end-user support, training, and safe technical escalation.

## Working in the demo
- Geisel Interview Mode: a guided five-minute public-data case study that connects audit evidence → prioritization → safe implementation/support → measurement, with explicit accuracy boundaries.
- Editable prioritization engine using institutional impact, visibility gap, competitive pressure, demand/capacity pressure, departmental web capacity, and implementation effort; sample inputs are clearly labeled illustrative.
- Server-side public URL auditor with SSRF-oriented private-network blocking, timeout, redirect validation, HTML-only checks, and response-size limit.
- Site Intelligence: bounded same-origin crawling, page inventory, linked PDF/Office document discovery + HEAD checks, architecture summary, JSON evidence export, and redirect-chain validation.
- Explainable SEO and GEO pass/review signals with proprietary weighting retained server-side.
- Metadata, canonical, robots/noindex, headings, internal/external links, image alt coverage, JSON-LD, authorship/date signals, Q&A patterns, and WordPress fingerprint checks.
- Evidence-linked issue severity and recommended fixes.
- JSON-LD draft generator.
- Editable roadmap factors with proprietary prioritization logic retained server-side.
- WordPress support/training workflow and role requirements matrix.
- Browser-local CSV import summaries for Search Console / Analytics exports; no upload or fake account connection.
- Repeatable QA gate covering JavaScript syntax, health, interview workflow presence, private-network blocking, and a real public-page audit.

## Interview review path
Use [GEISEL_INTERVIEW_WALKTHROUGH.md](GEISEL_INTERVIEW_WALKTHROUGH.md) for the five-minute hiring-manager walkthrough and [BUILD_AND_UPGRADE.md](BUILD_AND_UPGRADE.md) for the implementation trail.

Run `npm run qa` to execute the local quality gate. See the private repository [IP protection boundary](../IP_PROTECTION.md) for the public/private implementation split.

## Connector-ready, not represented as live
- Google Search Console
- Google Analytics
- Self-hosted WordPress
- WordPress.com

## Learning lab, not represented as production administration
- Apache and .htaccess concepts
- PHP / WordPress template safety
- MariaDB/MySQL application concepts

SearchSignal is an independent portfolio demonstration and is not affiliated with Dartmouth College or the Geisel School of Medicine.


## October 2 implementation upgrade

The interview build now adds an explicit implementation loop and larger-site operations surfaces:

- **Change Lab** — a synthetic page moves through detected issue → prepared WordPress-safe/HTML changes → sandbox apply → validation → re-audit. The UI and API explicitly state **No production site modified**.
- **Site Patterns** — groups duplicate-title/canonical and other recurring signals from the loaded bounded crawl, with public robots.txt/sitemap.xml checks.
- **Document Intelligence** — elevates PDF/Office files into a separate inventory with HTTP status, file size, Last-Modified, duplicate-filename, weak-link-text, and referencing-page signals. Accessibility remains a human-review requirement rather than an automated claim.
- **Interactive WordPress Support** — three realistic support cases walk through diagnosis, editor-safe steps, escalation, plain-language response, and reusable knowledge-base guidance.
- **Measurement workspace** — browser-local CSV analysis around a user-selected change date with 7/30/90-day before/after comparisons.
- **Progress & Reporting** — owner-aware roadmap register, weekly Web Architect update generation, and JSON/CSV/print-to-PDF export.
- **20K Scale Simulator** — synthetic 20,000-page / 15,000-document workload modeling for batches, rate limits, caching, checkpoints, pause/resume, and prioritization without crawling Geisel.
- **Requirements Coverage v2** — separates Implemented, Automated test, and Live verified evidence states.
- Additional technical signals include generic-link/form-label heuristics, crawl-delay controls, redirect-loop detection, richer document metadata, and audit JSON/CSV exports.

Automated QA now passes in GitHub CI/Portfolio Quality Control, and the upgraded standalone build has been redeployed to the production Vercel alias. Hosted smoke checks returned HTTP 200 for the app, health endpoint, Change Lab verification endpoint, and 20K scale-simulation endpoint. The Requirements Coverage screen still keeps feature-level **Live verified** states conservative until each specific deployed workflow is exercised.
