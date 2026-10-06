---
name: grimforge-workflow
description: Use for original episode planning, continuity, scene assets, local Forge preflight, rendering, narration, captions, and reviewable video exports.
---

# GrimForge Cinema

## Connection and access

This is a private app-workflow plugin attached to the owner's existing Grim Forge Commander V2 app. It reuses that verified app binding, secure tunnel, and intentionally no-auth local MCP server. Do not create a replacement tunnel, change to OAuth, or share this personal connection publicly. It does not provide a separate app-scoped security boundary or a public multi-user backend.

Use the connected Commander tools for laptop operations. Call Commander `health` first. The verified Forge Core loopback base on this laptop is `http://127.0.0.1:8787`; check `/api/health` and `/openapi.json` again before using an endpoint. See [local API reference](references/local-api.md). Inspect current schemas instead of inventing arguments. The API is reachable from the connected laptop, not from a public browser or the companion website. A GET method does not guarantee a side-effect-free route; inspect operational checks before using them in a read-only task.

If the local API is unavailable, inspect the installed launch instructions and configured paths. Preserve the existing installation; do not replace source, launch duplicate servers, terminate unrelated processes, or broaden persistent permissions merely to recover access.

Follow actions already authorized in the conversation. Keep changes reviewable, preserve originals/backups, and use configured project/output folders. Never expose secrets in commands, logs, exports, websites, or Git. The companion website explains the app; it does not execute laptop commands or ingest private cases.

## Creative workflow

Establish the original premise, runtime, visual route, and intended audience. Preserve the user's character and world anchors, Director's Notes, selected assets, narration, scene dialogue, and English-caption requirements. Keep Simple-mode choices concise; use Pro detail when the user needs scene control.

Start with a read-only Forge health check. For production readiness, inspect the current schema/source and use `/api/grimforge/preflight?animation_style=2.5d&production_mode=true` (or the requested supported style). In the verified build, this production-mode branch returned `auto_setup.changed: false`; default preflight can configure an image workflow. Do not call default preflight or scene-assets/status merely to check connectivity: scene-assets/status can start a configured ComfyUI service. Use operational checks only within the authorized production task.

Inspect available services before naming a renderer, model, or voice as connected. A production preflight pass is conditional on suitable scene assets and does not verify final media quality. Use the current local API schema for request fields. Long renders return or use jobs; retain the actual job ID and poll it instead of starting duplicate work. Keep outputs in the configured Forge projects/exports folders and preserve originals and production manifests.

Review actual imagery, character continuity, camera/framing, motion, narration, sound, caption timing, and final export. A passing process or fixture is not a production-quality episode. Report draft/fallback status honestly and improve observed failures before publication. Do not publish or incur cloud charges without authorization covering that action.
