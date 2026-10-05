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

## Current audit — October 5, 2026

Local repository audit: 109 checks passed; no failures. The portfolio manifest/syntax/encoding gate also passed. VocalForge documentation is now included in the inventory gate.

Actual laptop products were inspected separately. GrimForge's low-resolution image sources, scene-length subtitles and procedural Blender blocks do not meet final delivery quality. Verified final-label, caption, decoder, audio-assembly and motion-capability issues were fixed locally. A real 12.02-second episode completed and remained correctly labeled preview. Vocal export headroom and pitch confidence were fixed; 20 combined delivery/runtime/vocal regressions passed.

GitHub Actions jobs did not start because GitHub reported an account payment/spending-limit restriction. This is not a completed test run.

Workspace/Learn and the local app pages returned HTTP 200. Hosted GrimForge, WildTake and StudyForge HTML returned 200; this establishes availability only. The portfolio homepage returned 403 to an automated request; browser behavior is not established.

Full creative quality, anatomy accuracy, other apps' complete delivery workflows and source/live-version parity still require review.

## Previous audit — October 1, 2026

| Project | Delivery | Current QC evidence |
|---|---|---|
| Main employer portfolio | Live web | Production HTTP/title/meta/assets smoke passed |
| SearchSignal | Two live web surfaces + inspectable interview source | Geisel interview build: 6/6 Node QA passed; hosted homepage/assets/health/audit/site-scan/redirect checks passed; public Geisel audit + bounded crawl + HTTP→HTTPS redirect acceptance passed. Published Floot v2 remains live; latest v2 source parity is tracked separately as pending. |
| AJ Job Fisher | Live web + source | Production HTTP/title/meta smoke passed; Vite build covered by portfolio QC |
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
| Integrated Forge Suite | Private development repo + public showcase | Local repository checks passed; current GitHub Actions execution is account-blocked. Full Windows upgrade, visual and narrator quality remain acceptance items |

## Forge acceptance boundary

Forge's own acceptance documents distinguish **implemented**, **fixture-tested**, **live-engine-tested**, and **visually/user-reviewed** states. That distinction controls over any simpler portfolio badge. In particular, real Windows upgrade behavior and real Blender/ComfyUI/Kokoro output quality must not be described as verified until target-PC acceptance is complete.

## Maintenance rule

When an app is added or materially changed:

- add or update its entry in `portfolio/README.md`;
- add it to `scripts/portfolio_qc.py`;
- if it has a public URL, add it to `scripts/live_portfolio_smoke.py`;
- if it has a build/test process, add it to the GitHub Actions matrix;
- do not mark the app fully passed when an applicable real-engine, hardware, external-service, or human-review gate is still pending.
