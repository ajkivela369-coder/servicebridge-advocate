# Design Helper Recovery — Why 12ui Failed and How Forge Handles It

## What failed

The optional `12ui` design CLI was not already installed in the execution environment. Node.js, npm, and npx were present, but DNS resolution for `registry.npmjs.org` failed. Because `npx` downloads `@12ui/design` from the npm registry when it is not already cached, the install could not begin.

This is an **environment/network bootstrap failure**, not a Forge Core failure and not a problem with the generated teaching app. The same sandbox also could not resolve PyPI, Hugging Face, or GitHub during the diagnostic probe.

## Why this matters

A tool that must be downloaded at the exact moment we need it is a single point of failure. Even if the CLI is cached, 12ui's hosted design generation can still require internet/service access. Therefore it must be an accelerator, never a required runtime dependency.

## Permanent remedy

Forge now routes UI/design work through a shared design adapter:

1. **12ui available + service reachable** → use it as the high-quality design accelerator.
2. **12ui CLI missing but retained runtime exists** → restore the complete cached Node runtime from `FORGE_HOME/downloads/npm-packages`.
3. **Internet available but no retained runtime** → install once into `FORGE_HOME/tools/12ui`, centralize npm cache, and archive the complete working runtime for later restore.
4. **No network / hosted service unavailable** → use Forge's dependency-free local HTML/CSS/SVG design system.
5. **Previously approved templates available** → reuse retained templates without any generation service.

## Files added

- `forge_base/install_12ui.ps1` — restore-first 12ui installer.
- `forge_base/cache_12ui.ps1` — seeds the retained runtime/cache.
- `forge_core/services/design.py` — local fallback and status adapter.
- `FORGE_HOME/tools/12ui` — permanent restored/installed runtime.
- `FORGE_HOME/downloads/npm-packages` — archived complete runtime packages.
- `FORGE_HOME/downloads/npm-cache` — centralized npm dependency cache.
- `FORGE_HOME/templates/design` — retained local templates.

## Diagnostic improvement

Forge Doctor now records DNS readiness for:

- `registry.npmjs.org`
- `pypi.org`
- `huggingface.co`
- `github.com`

This lets Forge distinguish **"the tool is broken"** from **"the current environment cannot reach the package/model host."**

## Standing rule

A hosted design service may improve quality, but it can never be the only way Elias, MedForge, Evidence Auditor, GrimForge, or Forge Learn can render a usable interface.
