# Portfolio Quality Control

This document defines what "passes QC" means for the public portfolio. A green deployment or a successful unit test is useful evidence, but it is not treated as proof that every production workflow has been fully validated.

## Gates

A portfolio app is eligible for **QC PASS** only when the checks applicable to that app succeed:

1. **Repository integrity** — required source/readme files exist, JSON manifests parse, Python source compiles, and README text has no known mojibake markers.
2. **Build/test** — Vite projects build successfully; evaluator projects run their automated tests and benchmark scripts.
3. **Public smoke test** — a listed live URL returns HTML with HTTP 200, a non-empty title, viewport metadata, description metadata, loadable local JS/CSS assets, and no obvious server-error page text.
4. **Truth labeling** — seeded/demo data, independent portfolio work, connector-ready features, and learning-only surfaces are not presented as paid employment or production integrations.
5. **Safety / privacy boundary** — high-stakes medical, evidence, employment, or administrative tools retain human-review and privacy limitations.
6. **Special acceptance gates** — media quality, hardware integration, Windows installer behavior, or external-engine claims remain pending until actually tested on the target environment.

Automation lives in `.github/workflows/portfolio-qc.yml`, `scripts/portfolio_qc.py`, and `scripts/live_portfolio_smoke.py`.

## Current audit — 2026-10-01

| Project | Delivery | Current QC evidence |
|---|---|---|
| Main employer portfolio | Live web | Production HTTP/title/meta/assets smoke passed |
| SearchSignal | Two live web surfaces + inspectable interview source | Geisel interview build: 6/6 Node QA passed; hosted homepage/assets/health/audit/site-scan/redirect checks passed; public Geisel audit + bounded crawl + HTTP→HTTPS redirect acceptance passed. Published Floot v2 remains live; latest v2 source parity is tracked separately as pending. |
| Elias + Evidence Auditor | Live web + source | Production HTTP/title/meta smoke passed; core repo CI and evidence tests covered separately |
| NeuroEval | Live web + source/tests | Production smoke passed; pytest + benchmark CI |
| HealthQA Auditor | Live web + source/tests | Production smoke passed; pytest + benchmark CI |
| CiteGuard | Live web + source | Production smoke passed; Python syntax/source gate |
| PairRank | Live web + source | Production smoke passed; Python syntax/source gate |
| GrimForge Studio | Live web + local Forge successor | Production web smoke passed; source build gate. Full cinematic/voice quality is **not** considered passed by web smoke alone |
| StudyForge | Live web + source | Production smoke passed; Vite build gate |
| WildTake Studio | Live web + source | Production smoke passed; Vite build gate |
| CareFlow Research Lab | Source-only static demo | Repository/static-file gate; no public production URL currently claimed |
| Benchmark Forge | Source-only | Python syntax/source gate; no public production URL currently claimed |
| RaterLab | Source-only | Python syntax/source gate; no public production URL currently claimed |
| Integrated Forge Suite | Private development repo + public showcase | GitHub CI passed on the current imported baseline; real Windows upgrade, Blender/ComfyUI visual quality, and narrator quality remain target-PC acceptance items |

## Forge acceptance boundary

Forge's own acceptance documents distinguish **implemented**, **fixture-tested**, **live-engine-tested**, and **visually/user-reviewed** states. That distinction controls over any simpler portfolio badge. In particular, real Windows upgrade behavior and real Blender/ComfyUI/Kokoro output quality must not be described as verified until target-PC acceptance is complete.

## Maintenance rule

When an app is added or materially changed:

- add or update its entry in `portfolio/README.md`;
- add it to `scripts/portfolio_qc.py`;
- if it has a public URL, add it to `scripts/live_portfolio_smoke.py`;
- if it has a build/test process, add it to the GitHub Actions matrix;
- do not mark the app fully passed when an applicable real-engine, hardware, external-service, or human-review gate is still pending.

Archived: **AJ Job Fisher** was retired from the active portfolio on 2026-10-05. Its source/history remain preserved in `portfolio/aj-job-fisher/`, but it is no longer included in active live-smoke or release claims.


## October 6, 2026 — Commander, companion sites, and workflow plugins

| Delivery | Verification | Remaining acceptance |
|---|---|---|
| GFC server 2.0.0 and branded plugin package 1.0.1 | Healthy server; 46 registered tools; 75 qualification checks; successful package upload shown in ChatGPT | Current native catalog remains 10 tools; refreshed discovery must be inspected in a fresh connection |
| Four companion websites | Static HTML, assets, metadata, JSON, and JS checks; exact source pushes; private deployments succeeded | Browser visual/interaction review and public indexing pending; pages are owner-private |
| Three private app plugins 1.0.0 | Workflow validation and a read-only GrimForge forward test; saved manifests, binding, release IDs, and asset inventory verified | Owner installation/fresh-chat skill loading and full app outputs not yet exercised |
| Forge app connectivity | Read-only Core health/schema checks on target laptop | Multi-user isolation, paid-provider use, full renders, narration, and final media review remain separate |

The workflow forward test identified GET routes with potential side effects. Default GrimForge preflight can configure a workflow and scene-assets/status can start configured ComfyUI. Plugin guidance uses health/schema for connectivity and production-mode preflight only within the appropriate authorized task. No real evidence corpus was needed to validate connectivity.

The new Sites URLs are private and therefore are not added to the public HTTP smoke inventory at this snapshot. Add them and complete public smoke/visual checks when their audience becomes public. The private plugins reuse one GFC connection and do not grant separate app-scoped authorization.
