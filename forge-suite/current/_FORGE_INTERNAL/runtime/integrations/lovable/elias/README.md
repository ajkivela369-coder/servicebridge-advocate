# Elias Evidence Pro → Forge v0.4 patch
The Lovable turn partially landed before the workspace exhausted its credits. The live project now has a ForgePanel and Forge client, but its generated client points at several v0.3-style endpoints that do not match v0.4.

When the source is writable again, replace `src/lib/forge.ts` with this patched file. It uses the actual v0.4 endpoints:
- `/api/health`
- `/api/bridge/config`
- `/api/evidence/query`
- `/api/teach/render`
- `/api/vault/items`

Do not weaken HTTPS/browser security to make localhost work. Use the Forge Launcher or Export/Import fallback when direct loopback is blocked.
