# Forge v0.5 Workspace / Learn split

Forge Workspace is the production surface. Forge Learn is the teaching companion. They share Forge Core but do not share UI responsibilities.

Synchronization is enforced by `learning/learning_manifest.json` and `forge_base/learning_sync.py`. Every production feature with `learning_required: true` in `forge_base/feature_registry.json` must have a manifest entry containing a summary, concepts, workspace deep link and build story. `feature_gate.py` now includes this learning check.

Old `/static/apps/academy.html` links redirect to `/learn`.

## v0.5.2 UI preservation rule

Forge Core is infrastructure, not the product shell. Integrating or upgrading Core must not replace a working product interface with a diagnostic/test form.

Before release, `forge_base/ui_regression_gate.py` verifies that:

- Forge Workspace retains operational system/model/storage/recovery surfaces;
- Elias retains the evidence workspace, Vault/source inventory, search, chronology, linked claims, packet workflow, and Evidence Copilot;
- MedForge retains Image Lab, Mechanism Builder, Teach Me This, and Mechanism Flow;
- GrimForge retains Simple/Pro planning, presets, Surprise Me, continuity, Director's Notes, episode build, and local animatic controls;
- Forge Learn remains a separate synchronized companion rather than being merged into the production apps.
