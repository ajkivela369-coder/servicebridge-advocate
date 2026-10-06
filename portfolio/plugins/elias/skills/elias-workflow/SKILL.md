---
name: elias-workflow
description: Use for local Elias conversation, task planning, document questions, source-grounded reasoning, and movement into the specialist evidence workspace.
---

# Elias

## Connection and access

This is a private app-workflow plugin attached to the owner's existing Grim Forge Commander V2 app. It reuses that verified app binding, secure tunnel, and intentionally no-auth local MCP server. Do not create a replacement tunnel, change to OAuth, or share this personal connection publicly. It does not provide a separate app-scoped security boundary or a public multi-user backend.

Use the connected Commander tools for laptop operations. Call Commander `health` first. The verified Forge Core loopback base on this laptop is `http://127.0.0.1:8787`; check `/api/health` and `/openapi.json` again before using an endpoint. See [local API reference](references/local-api.md). Inspect current schemas instead of inventing arguments. The API is reachable from the connected laptop, not from a public browser or the companion website. A GET method does not guarantee a side-effect-free route; inspect operational checks before using them in a read-only task.

If the local API is unavailable, inspect the installed launch instructions and configured paths. Preserve the existing installation; do not replace source, launch duplicate servers, terminate unrelated processes, or broaden persistent permissions merely to recover access.

Follow actions already authorized in the conversation. Keep changes reviewable, preserve originals/backups, and use configured project/output folders. Never expose secrets in commands, logs, exports, websites, or Git. The companion website explains the app; it does not execute laptop commands or ingest private cases.

## Assistant workflow

Determine the user's intended outcome and whether the request is general assistance, a document question, or evidence review. Local Elias is an independent general assistant. The hosted Elias evidence demo has Evidence Auditor as a specialist workspace; do not conflate their builds or claim identical features.

Use the connected laptop tools for a read-only health/capability check, then inspect the current local API schema. Keep conversation messages and relevant context intact. Use evidence retrieval only for material the user has authorized you to inspect. Show source and page context when available, distinguish interpretation from source statements, and identify material gaps without inventing an answer.

Honor the selected local/cloud mode and current permissions. A ChatGPT subscription is not an API credential for the app. Do not read or print credential files. Avoid model changes or paid-provider requests without the necessary authorization. Confirm availability and inspect the returned answer before calling an integration verified.
