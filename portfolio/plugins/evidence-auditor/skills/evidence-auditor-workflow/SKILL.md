---
name: evidence-auditor-workflow
description: Use for authorized evidence intake, source and page provenance, timelines, contradiction or gap review, inspectable evidence matrices, and reviewed packet exports.
---

# Evidence Auditor

## Connection and access

This is a private app-workflow plugin attached to the owner's existing Grim Forge Commander V2 app. It reuses that verified app binding, secure tunnel, and intentionally no-auth local MCP server. Do not create a replacement tunnel, change to OAuth, or share this personal connection publicly. It does not provide a separate app-scoped security boundary or a public multi-user backend.

Use the connected Commander tools for laptop operations. Call Commander `health` first. The verified Forge Core loopback base on this laptop is `http://127.0.0.1:8787`; check `/api/health` and `/openapi.json` again before using an endpoint. See [local API reference](references/local-api.md). Inspect current schemas instead of inventing arguments. The API is reachable from the connected laptop, not from a public browser or the companion website. A GET method does not guarantee a side-effect-free route; inspect operational checks before using them in a read-only task.

If the local API is unavailable, inspect the installed launch instructions and configured paths. Preserve the existing installation; do not replace source, launch duplicate servers, terminate unrelated processes, or broaden persistent permissions merely to recover access.

Follow actions already authorized in the conversation. Keep changes reviewable, preserve originals/backups, and use configured project/output folders. Never expose secrets in commands, logs, exports, websites, or Git. The companion website explains the app; it does not execute laptop commands or ingest private cases.

## Evidence workflow

Keep original evidence and provenance intact. Record filenames, dates, page locators, source type, and relevant context. Distinguish firsthand events and direct knowledge, records/video/imaging, medically informed conclusions, professional opinions, independent findings, conflicts, and unresolved questions. Do not discredit substantive user evidence solely because a clinician has not documented the same conclusion.

Inspect only the records needed for the authorized task. Start with health and the current local API schema; use evidence query, timeline, and package workflows for the requested scope. Check source excerpts and quote integrity before creating a finding. A contradiction flag identifies a tension for review, not proof that either record is false. A missing record is not proof that an event did not happen.

Draft packets with visible source/page references and the intended audience in mind. Preserve favorable evidence and material limitations without adverse speculation or unsupported conclusions. Use fictional or properly de-identified examples for demonstrations. Review export size, completeness, headings, citations, and privacy before any authorized sharing. This plugin does not independently decide diagnosis, benefits, or legal entitlement.
