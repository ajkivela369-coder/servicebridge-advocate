from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import sys
import tempfile

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from servicebridge.local_runtime import (
    AssetCache,
    JobQueue,
    RuntimeMode,
    RuntimePolicy,
    runtime_snapshot,
)
from servicebridge.local_runtime.workers import worker_capabilities
from lessons import LESSONS, PIPELINE


st.set_page_config(
    page_title="Forge Systems Lab",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container{max-width:1500px;padding-top:1rem;padding-bottom:4rem}
[data-testid="stAppViewContainer"]{background:
 radial-gradient(circle at 87% 2%,rgba(71,167,181,.18),transparent 28%),
 radial-gradient(circle at 3% 7%,rgba(184,135,56,.12),transparent 24%),#071012}
[data-testid="stSidebar"]{background:#0a1518;border-right:1px solid #284047}
.kicker{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:#86a8ad}
.hero{font-family:Georgia,serif;font-size:2.25rem;font-weight:800;line-height:1.03}
.card{border:1px solid #29464d;background:#0b181b;border-radius:17px;padding:14px;margin:7px 0}
.ok{color:#a9e6c1}.miss{color:#e5c177}.dim{color:#91a7aa}
.badge{display:inline-block;padding:4px 8px;border:1px solid #385f67;border-radius:999px;background:#0b272c;color:#afe6ec;font-size:.7rem;margin:2px}
.flow{display:flex;gap:6px;align-items:center;overflow:auto;padding:8px 0}
.node{min-width:114px;border:1px solid #315861;background:#0b2024;border-radius:12px;padding:9px;text-align:center;font-size:12px}
.arrow{font-size:18px;color:#688b91}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="kicker">LOCAL-FIRST PLATFORM</div><div class="hero">Forge<br>Systems Lab</div>', unsafe_allow_html=True)
    st.caption("Teach, inspect, and troubleshoot the shared creditless runtime.")
    mode = st.radio("Runtime policy", [x.value for x in RuntimeMode], index=0)
    selected = st.selectbox(
        "Lesson",
        [f'{x["id"]} · {x["title"]}' for x in LESSONS],
    )
    lesson_idx = [f'{x["id"]} · {x["title"]}' for x in LESSONS].index(selected)

snapshot = runtime_snapshot(RuntimeMode(mode))
workers = [x.to_dict() for x in worker_capabilities()]

st.markdown('<div class="kicker">ONE RUNTIME · MANY APPS</div>', unsafe_allow_html=True)
st.title("Creditless infrastructure for Elias, GrimForge, MedForge & WildTake")
st.write(
    "The goal is not to remove every open-source dependency. It is to make paid/cloud services optional. "
    "When a local engine is missing, the apps should degrade to another local method instead of silently spending credits."
)

flow = '<div class="flow">' + ''.join(
    f'<div class="node">{name}</div>' + ('<div class="arrow">→</div>' if i < len(PIPELINE)-1 else '')
    for i, name in enumerate(PIPELINE)
) + '</div>'
st.markdown(flow, unsafe_allow_html=True)

status_tab, policy_tab, vault_tab, lesson_tab = st.tabs([
    "Runtime status",
    "Policy simulator",
    "Cache + queue sandbox",
    "How it works",
])

with status_tab:
    hw = snapshot["hardware"]
    a,b,c,d = st.columns(4)
    a.metric("CPU threads", hw["cpu_count"])
    b.metric("RAM", f'{hw["ram_gb"] or "?"} GB')
    c.metric("GPU VRAM", f'{hw["gpu_vram_gb"] or "?"} GB')
    d.metric("Compute tier", hw["tier"])

    st.markdown("**Local services**")
    rows = []
    for item in snapshot["services"]:
        rows.append({
            "Service": item["service_id"],
            "Kind": item["kind"],
            "Installed": "Yes" if item["installed"] else "No",
            "Healthy": "Yes" if item["healthy"] else "No",
            "Endpoint": item["endpoint"],
            "Notes": item["notes"],
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("**Local workers**")
    st.dataframe(
        [
            {
                "Worker": x["worker_id"],
                "Available": "Yes" if x["available"] else "No",
                "Mode": x["mode"],
                "Notes": x["notes"],
            }
            for x in workers
        ],
        use_container_width=True,
        hide_index=True,
    )

    if mode == RuntimeMode.CREDITLESS.value:
        st.success("Creditless invariant active: non-local model endpoints are blocked; cloud fallback is disabled.")

with policy_tab:
    st.subheader("Try the network guard")
    test_url = st.text_input("Endpoint", "http://127.0.0.1:8080/v1/chat/completions")
    external = st.checkbox("Allow external networking", value=False)
    fallback = st.checkbox("Allow cloud fallback", value=False)
    policy = RuntimePolicy(
        mode=RuntimeMode(mode),
        allow_external_network=external,
        allow_cloud_fallback=fallback,
    )
    if st.button("Check endpoint", type="primary"):
        try:
            policy.assert_url_allowed(test_url)
            st.success("Allowed by the current runtime policy.")
        except Exception as exc:
            st.error(str(exc))

    st.caption(
        "Creditless Mode ignores attempts to enable cloud fallback for non-local model endpoints. "
        "Switching to Hybrid/Cloud is an explicit policy change."
    )

with vault_tab:
    st.subheader("Asset Vault + persistent job queue")
    st.caption("This sandbox uses temporary local storage and demonstrates the exact shared runtime objects.")
    demo_root = Path(tempfile.gettempdir()) / "forge-systems-lab-runtime"
    content = st.text_area("Demo asset", "This could be OCR output, a narration clip, segmentation mask, or rendered frame.")
    kind = st.selectbox("Asset kind", ["text", "ocr", "audio", "image", "mask", "render"])

    if st.button("Store asset"):
        with AssetCache(demo_root / "assets") as cache:
            saved = cache.put(
                content.encode("utf-8"),
                kind=kind,
                suffix=".txt",
                provenance={"app": "forge-systems-lab", "runtime_mode": mode},
            )
        st.json(saved)

    payload_text = st.text_input("Job payload", "render scene 04")
    q = JobQueue(demo_root / "jobs.sqlite3")
    if st.button("Queue local job"):
        job_id = q.enqueue("demo", {"instruction": payload_text})
        st.session_state["last_job"] = job_id
    if st.session_state.get("last_job"):
        st.json(q.get(st.session_state["last_job"]))
    q.close()

    st.info(
        "The asset hash lets every app reuse identical work. The job database keeps long local tasks separate from browser/UI state."
    )

with lesson_tab:
    lesson = LESSONS[lesson_idx]
    st.markdown(f'<div class="kicker">LESSON {lesson["id"]}</div>', unsafe_allow_html=True)
    st.header(lesson["title"])
    st.write(lesson["plain"])
    st.markdown("**Why it matters**")
    st.write(lesson["why"])
    c1,c2 = st.columns(2)
    c1.warning("When it fails\n\n" + lesson["failure"])
    c2.info("Repair path\n\n" + lesson["fix"])

    module = importlib.import_module(lesson["module"])
    obj = getattr(module, lesson["function"])
    try:
        source = inspect.getsource(obj)
    except Exception as exc:
        source = f"# Could not load source: {exc}"
    with st.expander(f'Actual code · {lesson["module"]}.{lesson["function"]}', expanded=True):
        st.code(source, language="python")

st.caption("Forge Systems Lab · live companion to the ServiceBridge Local Runtime")
