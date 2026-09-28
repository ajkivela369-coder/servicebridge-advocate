from __future__ import annotations

import json
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from forge_core import ForgeCore, ForgeSDK
from forge_core.model_profiles import register_present_profiles, staged_profile_status
from forge_core.process import ForgeProcessManager
from forge_core.settings import ForgeSettings
from servicebridge.local_runtime.offline import build_offline_pack


st.set_page_config(
    page_title="Forge Launcher",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container{max-width:1550px;padding-top:1rem;padding-bottom:4rem}
[data-testid="stAppViewContainer"]{background:
 radial-gradient(circle at 92% 0%,rgba(43,123,132,.16),transparent 27%),
 radial-gradient(circle at 3% 4%,rgba(167,126,55,.10),transparent 22%),#081012}
[data-testid="stSidebar"]{background:#0b1518;border-right:1px solid #263b40}
.f-eyebrow{font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;color:#8aa3a8;font-weight:800}
.f-title{font-family:Georgia,serif;font-size:2rem;font-weight:800;margin:0;line-height:1.05}
.f-card{border:1px solid #2a4147;background:rgba(10,22,25,.94);border-radius:16px;padding:14px;margin:8px 0}
.f-good{color:#a9dfc0}.f-warn{color:#e3c77e}.f-bad{color:#ef9d91}.f-muted{color:#91a6aa;font-size:.82rem}
.f-badge{display:inline-block;border:1px solid #36565e;background:#0b252b;color:#b6e3e8;border-radius:999px;padding:4px 8px;margin:2px;font-size:.7rem}
</style>
""",
    unsafe_allow_html=True,
)

settings_store = ForgeSettings(ROOT / "private_data/forge/settings.json")
settings = settings_store.load()
manager = ForgeProcessManager(repo_root=ROOT, data_root=ROOT / "private_data/forge")
forge = ForgeSDK.for_app("forge_launcher")


def refresh_state():
    try:
        return forge.status()
    except Exception:
        # In-process SDK still gives a useful state even if the HTTP daemon is down.
        return ForgeCore().status()


state = refresh_state()
memory = state.get("memory_budget", {})
hardware = state.get("hardware", {})

with st.sidebar:
    st.markdown('<div class="f-eyebrow">ONE BACKEND · FOUR APPS</div><div class="f-title">Forge Launcher</div>', unsafe_allow_html=True)
    st.caption("Forge Core v0.4")
    mode_label = st.radio(
        "Runtime policy",
        ["Local Only", "Hybrid"],
        index=0 if settings.get("mode") == "creditless" else 1,
    )
    new_mode = "creditless" if mode_label == "Local Only" else "hybrid"
    if new_mode != settings.get("mode"):
        settings["mode"] = new_mode
        settings_store.save(settings)
        st.toast("Forge runtime policy saved.")

    core_status = manager.status("forge_core")
    if core_status["healthy"]:
        st.success("Forge Core connected")
        if st.button("Stop Forge Core", use_container_width=True):
            manager.stop("forge_core")
            st.rerun()
    else:
        st.warning("Forge Core daemon stopped")
        if st.button("Start Forge Core", type="primary", use_container_width=True):
            try:
                manager.start("forge_core", forge_mode=settings["mode"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.button("Run Doctor", use_container_width=True):
        st.session_state["doctor_state"] = refresh_state()

    st.caption("Lovable deployment: blocked until workspace credits are available. Local Launcher remains fully usable.")


overview, memory_tab, models_tab, services_tab, apps_tab, vault_tab, jobs_tab, recovery_tab, settings_tab = st.tabs([
    "Overview",
    "Hardware & Memory",
    "Models",
    "Services",
    "Apps",
    "Forge Vault",
    "Jobs & Cache",
    "Backup & Recovery",
    "Settings",
])

with overview:
    st.markdown('<div class="f-eyebrow">FORGE CORE V0.4</div>', unsafe_allow_html=True)
    st.title("One Backend, Four Apps")
    st.write(
        "Elias, Evidence Auditor, MedForge, and GrimForge consume one Forge SDK/API. "
        "Forge owns model selection, memory admission, local workers, shared sources, cache, and provenance."
    )

    a,b,c,d = st.columns(4)
    a.metric("Mode", "Local Only" if settings["mode"] == "creditless" else "Hybrid")
    a.caption("Cloud cannot be selected directly by an app.")
    b.metric("RAM free", f'{hardware.get("ram_available_gb") or "?"} GB')
    b.caption(f'Total: {hardware.get("ram_gb") or "?"} GB')
    c.metric("VRAM free", f'{hardware.get("gpu_vram_free_gb") or "?"} GB')
    c.caption(f'Total: {hardware.get("gpu_vram_gb") or "?"} GB')
    d.metric("Memory pressure", str(memory.get("pressure","unknown")).upper())
    d.caption(f'Reserved headroom: {memory.get("reserve_ram_gb","?")} GB RAM / {memory.get("reserve_vram_gb","?")} GB VRAM')

    st.markdown("**App dependency map**")
    app_rows = state.get("apps", [])
    st.dataframe(app_rows, use_container_width=True, hide_index=True)

    st.markdown("**Current reservations**")
    reservations = state.get("reservations", [])
    if reservations:
        st.dataframe(reservations, use_container_width=True, hide_index=True)
    else:
        st.caption("No Forge model memory leases are active.")

with memory_tab:
    st.subheader("RAM / VRAM admission controller")
    st.caption(
        "Forge uses live free memory, not advertised totals. It reserves headroom before admitting a model/job."
    )
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Usable RAM", f'{memory.get("usable_ram_gb","?")} GB')
    m2.metric("RAM reserve", f'{memory.get("reserve_ram_gb","?")} GB')
    m3.metric("Usable VRAM", f'{memory.get("usable_vram_gb","?")} GB')
    m4.metric("VRAM reserve", f'{memory.get("reserve_vram_gb","?")} GB')
    st.json({
        "policy": [
            "simple tasks → small/fast model",
            "complex reasoning → larger model only when SAFE/TIGHT",
            "vision → dedicated VLM",
            "background tasks → CPU where practical",
            "never oversubscribe Forge VRAM budget",
            "unload oldest idle model before admitting a larger one",
            "deterministic fallback beats a crash",
        ],
        "hardware": hardware,
    })

    st.markdown("**Ask Forge what fits**")
    cap = st.selectbox("Capability", ["reason","code","vision","embed"])
    work = st.selectbox("Work class", ["tiny","standard","heavy"], index=1)
    if st.button("Plan model", type="primary"):
        try:
            plan = forge.select_model(cap, work_class=work)
            st.json(plan)
            if plan.get("reservation_id"):
                forge.unload(plan["reservation_id"])
        except Exception as exc:
            st.error(str(exc))

with models_tab:
    st.subheader("Shared local model vault")
    st.caption("No app owns its own model list. Forge stages roles and registers files that actually exist on disk.")
    profiles = staged_profile_status(ROOT / "config/forge_model_profiles.json")
    st.dataframe(profiles, use_container_width=True, hide_index=True)

    c1,c2 = st.columns(2)
    if c1.button("Register present staged models", use_container_width=True):
        registered = register_present_profiles(
            ForgeCore().paths.model_catalog,
            ROOT / "config/forge_model_profiles.json",
        )
        st.success("Registered: " + (", ".join(registered) if registered else "none present yet"))
    if c2.button("Refresh model fit", use_container_width=True):
        st.rerun()

    registered_models = ForgeCore().list_models()
    st.markdown("**Registered models + live fit**")
    if registered_models:
        st.dataframe(registered_models, use_container_width=True, hide_index=True)
    else:
        st.info("Model roles are staged, but no model files have been registered yet.")

    st.warning(
        "Online model download/update is intentionally not automatic in this milestone. "
        "Forge will add controlled downloader/update support after recovery is proven."
    )

with services_tab:
    st.subheader("Forge capability router")
    rows = forge.capabilities()
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("A missing premium/generative capability must degrade to the listed local fallback.")

with apps_tab:
    st.subheader("Apps")
    st.caption("Start/stop from here; normal use should not require PowerShell.")
    statuses = {x["process_id"]:x for x in manager.all_status()}
    for process_id in ["elias","evidence_auditor","medforge","grimforge"]:
        row = statuses[process_id]
        cols = st.columns([0.24,0.20,0.18,0.18,0.20])
        cols[0].markdown(f'**{row["name"]}**')
        cols[1].write("Healthy" if row["healthy"] else "Stopped")
        cols[2].caption("Backend: Forge Core")
        if row["healthy"] or row["alive"]:
            if cols[3].button("Stop", key=f"stop_{process_id}", use_container_width=True):
                manager.stop(process_id)
                st.rerun()
            cols[4].link_button("Open", row["open_url"], use_container_width=True)
        else:
            if cols[3].button("Start", key=f"start_{process_id}", type="primary", use_container_width=True):
                try:
                    if not manager.status("forge_core")["healthy"]:
                        manager.start("forge_core", forge_mode=settings["mode"])
                    manager.start(process_id, forge_mode=settings["mode"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            cols[4].caption(row["open_url"])

with vault_tab:
    st.subheader("Forge Vault")
    vault = forge.vault_status()
    v1,v2,v3 = st.columns(3)
    v1.metric("Unique originals", vault.get("source_count", 0))
    v2.metric("App references", vault.get("reference_count", 0))
    v3.metric("Derived assets", vault.get("derived_count", 0))
    st.json(vault)
    st.info(
        "Apps reference one immutable SHA-256 original by source ID. "
        "Generated/derived files point back to that source rather than replacing it."
    )

with jobs_tab:
    st.subheader("Jobs & Cache")
    jobs = forge.jobs()
    if jobs:
        st.dataframe(jobs, use_container_width=True, hide_index=True)
    else:
        st.caption("No Forge jobs recorded.")
    cache = forge.cache_status()
    st.json(cache)

with recovery_tab:
    st.subheader("Backup & disaster recovery")
    recovery_state = forge.backup_status()
    status = str(recovery_state.get("status", "NOT_RUN"))
    if status == "PASS":
        st.success("Recovery PASS · a clean restored copy rebuilt and rendered the verification project.")
    elif status == "PARTIAL":
        st.warning("Recovery PARTIAL · inspect the failed acceptance checks below.")
    else:
        st.warning(
            "Recovery is not marked PASS until a verified pack is restored into a clean directory "
            "and the restored code actually renders the representative MP4."
        )
    st.json(recovery_state)

    backup_root = Path(settings.get("backup_root", "./private_data/forge_backups"))
    if not backup_root.is_absolute():
        backup_root = ROOT / backup_root
    backup_root.mkdir(parents=True, exist_ok=True)
    default_pack = backup_root / "forge-creditless-offline-pack.zip"

    include_models = st.checkbox(
        "Include registered model files in offline pack",
        value=False,
        help="Model files can make the backup very large. They are never swept in unless you explicitly enable this.",
    )
    if st.button("Build verified offline pack", use_container_width=True):
        try:
            result = build_offline_pack(
                default_pack,
                repo_root=ROOT,
                model_catalog=ForgeCore().paths.model_catalog,
                workflow_catalog=ROOT / "private_data/local_runtime/workflows.json",
                include_models=include_models,
            )
            st.session_state["last_backup_result"] = result
            st.success(f'Offline pack built: {result["entry_count"]} verified manifest entries.')
        except Exception as exc:
            st.error(f"Backup build failed: {exc}")

    if st.session_state.get("last_backup_result"):
        st.json(st.session_state["last_backup_result"])

    pack_path = st.text_input(
        "Recovery pack",
        str(default_pack),
        help="Forge verifies every manifest hash before attempting the restore.",
    )
    network_confirmed = st.checkbox(
        "External internet is actually disabled for this drill",
        value=False,
        help="Do not check this merely to obtain PASS. Forge records this as an acceptance condition.",
    )
    primary_exe = st.text_input(
        "Primary executable to remove from recovery PATH",
        "ollama",
    )

    r1, r2 = st.columns(2)
    if r1.button("Verify pack", use_container_width=True):
        try:
            st.session_state["backup_verify"] = forge.verify_backup(pack_path)
        except Exception as exc:
            st.error(f"Pack verification failed: {exc}")
    if r2.button("Run recovery drill", type="primary", use_container_width=True):
        try:
            st.session_state["recovery_result"] = forge.recovery_drill(
                pack_path,
                network_isolation_confirmed=network_confirmed,
                primary_executable=primary_exe,
            )
        except Exception as exc:
            st.error(f"Recovery drill failed: {exc}")

    if st.session_state.get("backup_verify"):
        st.markdown("**Pack verification**")
        st.json(st.session_state["backup_verify"])
    if st.session_state.get("recovery_result"):
        st.markdown("**Latest drill result**")
        st.json(st.session_state["recovery_result"])

    st.caption(
        "Acceptance chain: archive hashes → empty restore target → restored source compiles → "
        "Forge imports from restored copy → primary executable absent from PATH → external network isolation confirmed → "
        "representative project renders to a non-empty MP4."
    )

with settings_tab:
    st.subheader("Launcher settings")
    editable = dict(settings)
    editable["forge_core_url"] = st.text_input("Forge Core URL", editable.get("forge_core_url","http://127.0.0.1:8765"))
    editable["storage_root"] = st.text_input("Storage root", editable.get("storage_root","./private_data/forge"))
    editable["backup_root"] = st.text_input("Backup root", editable.get("backup_root","./private_data/forge_backups"))
    editable["model_policy"] = st.selectbox(
        "Model policy",
        ["eco","balanced","max-local"],
        index=["eco","balanced","max-local"].index(editable.get("model_policy","balanced"))
        if editable.get("model_policy","balanced") in ["eco","balanced","max-local"] else 1,
    )
    editable["auto_unload_idle_models"] = st.toggle(
        "Auto-unload idle models",
        value=bool(editable.get("auto_unload_idle_models", True)),
    )
    editable["idle_unload_minutes"] = st.number_input(
        "Idle unload after minutes",
        min_value=1,
        max_value=120,
        value=int(editable.get("idle_unload_minutes", 10)),
    )
    if st.button("Save settings", type="primary"):
        editable["mode"] = settings["mode"]
        settings_store.save(editable)
        st.success("Forge Launcher settings saved.")

if st.session_state.get("doctor_state"):
    with st.expander("Doctor result", expanded=True):
        st.json(st.session_state["doctor_state"])

st.caption("Forge Launcher · local control plane · Lovable publish pending workspace credits")
