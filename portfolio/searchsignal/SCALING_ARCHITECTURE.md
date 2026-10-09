# SearchSignal scale architecture

The public demo intentionally caps synchronous crawling. A 20,000-page / 15,000-document estate should be processed as a resumable program, not one long browser request.

## Production crawl model

1. **Seed inventory** from robots.txt, XML sitemaps, known subsite roots, analytics landing pages, CMS exports, and department-provided URL lists.
2. **Normalize and deduplicate** URLs before enqueueing.
3. **Partition by host/subsite** so robots rules and rate limits are enforced per host.
4. **Persist robots policy** including user-agent rules and crawl-delay.
5. **Queue crawl jobs** with bounded concurrency and per-host token buckets.
6. **Checkpoint continuously** so a crawl can resume after failures or deployment restarts.
7. **Store page/document fingerprints** for duplicate-title, duplicate-description and duplicate-content clustering.
8. **Record link edges** separately from page records so crawl depth, isolated clusters and orphan-risk analysis can be recomputed without refetching content.
9. **Split document processing** into a separate queue because PDFs/DOCX files have different size, extraction and accessibility costs than HTML.
10. **Join analytics after crawling** instead of using analytics as the crawl source of truth. High-impression / position 8–15 pages can then be prioritized against technical/content findings.
11. **Version findings** so remediation can be verified with before/after evidence rather than overwriting the original audit.
12. **Throttle expensive checks** such as Lighthouse/PageSpeed, visual regression, or AI evaluation to priority URLs.

## Suggested data model

- `crawl_run`: scope, start/end, robots snapshot, settings, status
- `url`: normalized URL, host, subsite, content type, owner/status metadata
- `page_snapshot`: status, title, meta, canonical, headings, schema, content hash, bytes, timings
- `document_snapshot`: metadata, extraction/accessibility indicators, content hash
- `link_edge`: source URL → destination URL, anchor/context
- `finding`: issue type, severity, evidence, owner, effort, approval boundary, remediation status
- `analytics_fact`: query/page/date metrics from Search Console or GA exports/APIs
- `verification`: post-fix crawl evidence and measured change

## Concurrency and crawl ethics

- Respect `robots.txt` and crawl-delay.
- Default to one worker when a site requests a delay; use modest parallelism only when policy permits it.
- Separate hosts/subsites into independent rate-limit buckets.
- Back off on 429/503 responses and suspend a host after repeated errors.
- Never use the public demo to stress-test somebody else's infrastructure.

## Public-demo boundary

The hosted SearchSignal app proves the crawler, sitemap/robots logic, document audit, link graph, duplicate detection, context-aware GEO, imports, and remediation workflows on bounded samples.

The **20K + 15K Scale Lab** exercises large-record triage locally in the browser using synthetic records. It is not presented as evidence that 35,000 real institutional resources were crawled.

This distinction is intentional: scale architecture and operational restraint are part of the demonstration.
