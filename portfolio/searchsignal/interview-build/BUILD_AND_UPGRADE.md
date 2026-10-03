# SearchSignal Interview Build — Build + Upgrade History

1. Preserved the existing independent SEO/GEO operations demo and its truth-labeling boundaries.
2. Added **Geisel Interview Mode**, a guided five-minute workflow connecting audit evidence, prioritization, safe implementation/support, training, and measurement.
3. Added an editable prioritization engine using impact, visibility gap, competition, demand/capacity pressure, departmental web capacity, and implementation effort.
4. Labeled all roadmap starting values as illustrative rather than Geisel internal data.
5. Kept the public URL auditor server-side with private-network blocking, redirect checks, timeout limits, HTML-only validation, and bounded response size.
6. Ran a live public Geisel homepage audit successfully after the interview changes.
7. Redesigned the interview build around a restrained academic/technical visual system while retaining SearchSignal identity and avoiding Dartmouth/Geisel brand impersonation.
8. Added dedicated navigation and KPI assets, responsive layouts, visible focus states, and interview-oriented information hierarchy.
9. Captured and visually reviewed the dashboard, Geisel Interview Mode, and Priority Roadmap at a 1440×900 viewport.
10. Added **Site Intelligence** with a bounded same-origin crawl, page inventory, linked document discovery/checks, architecture summary, JSON evidence export, and redirect-chain validation.
11. Verified the Site Intelligence backend against the public Geisel site: a six-page sample completed without fetch errors, and the HTTP homepage redirect resolved through 301 → HTTPS → 200.
12. Added browser-local Search Console / Analytics CSV summaries so the import controls are functional without pretending authenticated account access.
13. Added a repeatable `npm run qa` gate; the current suite checks syntax, health, interview workflow, private-network protection, public auditing, site scanning, and redirect validation.
14. Kept the richer published Floot v2 separate: this local build does not supersede v2 until source access reopens and parity is verified.

24. Added Change Lab: synthetic current-page inspection, exact before/after implementation diff, sandbox-only apply, validation, and re-audit. The workflow explicitly states that no production site is modified.
25. Added Site Patterns, including duplicate title/canonical clusters derived from the bounded crawl and public robots.txt/sitemap.xml status checks.
26. Promoted linked files into Document Intelligence with HTTP metadata, file-size and duplicate-name signals, Last-Modified review signals, and referencing-page counts; document accessibility remains a separate human-testing boundary.
27. Rebuilt WordPress Support as an interactive diagnosis → editor-safe steps → escalation → plain-language response → knowledge-base workflow across three realistic support scenarios.
28. Reworked analytics imports into browser-local 7/30/90-day before/after comparisons around a chosen change date, with plain-English reporting and print/save-to-PDF support.
29. Added Progress & Reporting with an owner-aware roadmap register, generated weekly Web Architect update, and JSON/CSV exports.
30. Added a synthetic 20K-page / 15K-document scale simulator for batching, rate limits, caching, checkpoints, pause/resume, modeled issue clusters, and prioritization without a production crawl.
31. Upgraded Requirements Coverage so implementation, automated-test coverage, and live verification are independent evidence states.
32. Added supporting technical controls: polite crawl delay, redirect-loop detection, generic-link/form-label heuristic signals, richer document headers, and audit JSON/CSV exports.
33. Ran GitHub CI and Portfolio Quality Control successfully, visually smoke-tested the upgraded Change Lab, WordPress Support, Scale Simulator, and Requirements Coverage surfaces, verified preview API behavior, then manually redeployed the standalone Vercel project to production. Production smoke returned HTTP 200 for the app, health endpoint, Change Lab verify action, and 20K/15K scale simulation.

34. Fixed audit scoring for blocked/error/challenge responses after a live Prime Video test exposed a false-positive score. Unscorable responses now suppress SEO/GEO scores, show retrieval diagnostics, and mark page-level checks N/A; zero-image pages no longer receive automatic alt-text credit. Regression QA passed 17/17 before production redeploy.

35. Added Browser-rendered Audit mode using headless Chromium + Puppeteer Core. The workflow uses the normal server fetch first, then supports explicit rendered auditing for JavaScript-heavy/hash-routed pages. Private-network requests are blocked during subresource loading, media/fonts are skipped, and rendered DOM output reuses the same explainable SEO/GEO analyzer.
36. Added route-integrity safeguards: if client-side rendering redirects a requested content route to an authentication/login wall, SearchSignal suppresses SEO/GEO scoring and reports the route mismatch rather than grading the login wall.
37. Preview-tested the rendered auditor on GeForce NOW `#/layout/games`; the Vercel preview rendered the requested route successfully and returned a browser-rendered audit with retrieval metadata.

38. Added a content-type classifier so SearchSignal selects a scoring model based on observed evidence rather than forcing every URL through the generic webpage rubric.
39. Added a Video Evidence Extractor for creator/channel, duration, publication date, thumbnail, embed/player metadata, Open Graph video metadata, microdata, topic tags, interactions, chapters, and transcript signals.
40. Added primary-content isolation for video pages. Platform navigation, comments, recommendation feeds, and other shell text remain observable but are excluded from the primary video content word count used for scoring.
41. Added Video SEO/GEO v1 rubrics with video-specific checks for metadata, creator identity, chapters, transcript availability/extractability, topic/entity metadata, freshness, and primary-content extraction.
42. Added YouTube transcript loading support, including current `transcript-segment-view-model` markup, plus deduplicated chapter intelligence.
43. Added Smart Audit automatic fallback: server fetch first, then rendered Chromium only when the URL is hash-routed, unscorable, classified as video/application, or looks like a thin JavaScript shell.
44. Added rendered-audit concurrency limits and a short-lived cache to reduce repeated Chromium work. Existing private-network blocking and auth-wall score suppression remain in force.
45. Local QA passed 22/22 after the smart-audit and video-intelligence upgrade. Live stress tests correctly classified and analyzed the supplied YouTube watch page and continued to suppress GeForce NOW scoring when its requested route redirected to a login wall.
