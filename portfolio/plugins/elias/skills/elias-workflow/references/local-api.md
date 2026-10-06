# Verified local API reference

Discovery date: 2026-10-06. Forge Core `/api/health` returned `ok: true` on port 8787 with local-only mode. The following route registrations and required-field names were read from that running server’s `/openapi.json`; they do not prove final output quality. Re-fetch the schema before a call.

| Method | Path | Required JSON fields |
|---|---|---|
| GET | `/api/health` | See live schema; no required JSON fields recorded |
| GET | `/api/capabilities` | See live schema; no required JSON fields recorded |
| POST | `/api/elias/chat` | `messages` |
| POST | `/api/evidence/query` | `question` |

Use the Commander Python executable or another existing allowlisted HTTP client on the laptop. `http://127.0.0.1:8787` is a laptop loopback address, not a public MCP endpoint. Keep response sizes bounded. Do not retrieve private timelines or packets merely to test connectivity. Use `/api/health` and `/openapi.json` for initial connection inspection. Production-mode preflight with `production_mode=true` was inspected and returned `auto_setup.changed: false`; default preflight may configure an image workflow. Scene-assets/status may start configured ComfyUI and is not a read-only connectivity probe. For generation, operational service checks, evidence processing, file writes, export, or publication, use the user-authorized task scope.
