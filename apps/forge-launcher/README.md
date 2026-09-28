# Forge Launcher

Local desktop-style control plane for **Forge Core v0.4 — One Backend, Four Apps**.

Run:

```bash
python -m pip install -e '.[api]'
python -m pip install -r apps/forge-launcher/requirements.txt
streamlit run apps/forge-launcher/app.py
```

Launcher responsibilities:
- Local Only / Hybrid policy
- start/stop Forge Core
- start/stop Elias, Evidence Auditor, MedForge, GrimForge
- live RAM/VRAM budget and pressure
- SAFE/TIGHT/BLOCKED model planning
- staged model roles and registration
- shared Forge Vault status
- jobs/cache health
- backup/recovery acceptance status
- one place for Forge endpoints and storage policy

The Lovable-hosted version is a control-plane target, not a GPU host. Heavy inference remains local.
