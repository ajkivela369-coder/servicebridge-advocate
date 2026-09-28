from __future__ import annotations

import inspect
from pathlib import Path
import sys

import numpy as np
import streamlit as st

HERE = Path(__file__).resolve().parent
MEDFORGE = HERE.parent / "medforge-imaging-studio"
if str(MEDFORGE) not in sys.path:
    sys.path.insert(0, str(MEDFORGE))

import med_engine
import med_export
import med_io
import med_masks
import med_segmentation
import med_volume
from lessons import LESSONS, PIPELINE


MODULES = {
    "med_export": med_export,
    "med_io": med_io,
    "med_masks": med_masks,
    "med_volume": med_volume,
    "med_segmentation": med_segmentation,
    "med_engine": med_engine,
}

st.set_page_config(
    page_title="MedForge Build Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {--cyan:#72c7d3;--paper:#e9f5f6;--ink:#071012;--gold:#c8a45b}
.block-container{max-width:1500px;padding-top:1rem;padding-bottom:4rem}
[data-testid="stAppViewContainer"]{background:
 radial-gradient(circle at 90% 0%,rgba(87,170,187,.16),transparent 28%),
 radial-gradient(circle at 3% 8%,rgba(202,164,91,.11),transparent 24%),#071012}
[data-testid="stSidebar"]{background:#0b1618;border-right:1px solid #284247}
.lab-kicker{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:#88a9ae}
.lab-title{font-family:Georgia,serif;font-size:2.25rem;font-weight:800;line-height:1.05}
.card{border:1px solid #29474d;background:#0b171a;border-radius:18px;padding:15px;margin:8px 0}
.badge{display:inline-block;border:1px solid #37636b;background:#0d272c;color:#bce9ef;padding:5px 9px;border-radius:999px;font-size:.72rem;margin:2px}
.fix{border-left:3px solid #72c7d3;padding:10px 12px;background:#0a2024;border-radius:0 12px 12px 0}
.fail{border-left:3px solid #c8a45b;padding:10px 12px;background:#211b0e;border-radius:0 12px 12px 0}
.flow{display:flex;gap:7px;align-items:center;overflow:auto;padding:10px 0}
.node{min-width:116px;border:1px solid #315963;border-radius:12px;padding:10px;text-align:center;background:#0b1e22;font-size:12px}
.arrow{color:#6f969c;font-size:20px}
</style>
""",
    unsafe_allow_html=True,
)


def phantom_volume(size=48):
    z, y, x = np.mgrid[:size, :size, :size]
    c = (size - 1) / 2
    sphere = ((x-c)**2 + (y-c)**2 + (z-c)**2) < (size*0.28)**2
    smaller = ((x-(c+9))**2 + (y-(c-5))**2 + (z-c)**2) < (size*0.11)**2
    tube = ((x-(c-8))**2 + (y-(c+7))**2) < (size*0.06)**2
    v = np.zeros((size,size,size), dtype=np.float32)
    v[sphere] = 600
    v[smaller] = 1100
    v[tube] = 850
    v += (z.astype(np.float32) / size) * 80
    return v


with st.sidebar:
    st.markdown('<div class="lab-kicker">PARALLEL LEARNING APP</div><div class="lab-title">MedForge<br>Build Lab</div>', unsafe_allow_html=True)
    st.caption("Learn the exact pipeline used by MedForge Imaging Studio.")
    mode = st.radio("Depth", ["Beginner", "Technical"], horizontal=True)
    st.divider()
    lesson_titles = [f'{x["id"]} · {x["title"]}' for x in LESSONS]
    selected_title = st.selectbox("Jump to lesson", lesson_titles)
    selected_idx = lesson_titles.index(selected_title)
    st.divider()
    st.caption("The code panels are read from the same MedForge modules used by the real app.")

st.markdown('<div class="lab-kicker">Visual + code + why it matters</div>', unsafe_allow_html=True)
st.title("How MedForge is built")
st.write(
    "This app teaches the workflow while the main MedForge app performs it. "
    "The goal is to make every transformation traceable: what came from the source, "
    "what the software changed for display, what AI may suggest, and what remains a hypothesis."
)

flow_html = '<div class="flow">' + ''.join(
    f'<div class="node">{name}</div>' + ('<div class="arrow">→</div>' if i < len(PIPELINE)-1 else '')
    for i, name in enumerate(PIPELINE)
) + '</div>'
st.markdown(flow_html, unsafe_allow_html=True)

overview, sandbox, lessons_tab, tests_tab = st.tabs([
    "Pipeline map",
    "3D sandbox",
    "Step-by-step lessons",
    "Testing strategy",
])

with overview:
    st.subheader("What travels through the pipeline")
    a,b,c = st.columns(3)
    with a:
        st.markdown('<div class="card"><span class="badge">TRUTH LAYER</span><h3>Source evidence</h3>'
                    '<p>Original image pixels, study geometry, source notes, and record-backed citations.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><span class="badge">DERIVED</span><h3>Display + measurements</h3>'
                    '<p>Windowed images, reformatted views, labels, measurements, masks, and reviewed segmentations.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="card"><span class="badge">ILLUSTRATIVE</span><h3>Mechanism synthesis</h3>'
                    '<p>Motion, loading, compression, traction, or other reconstructed hypotheses used for explanation.</p></div>', unsafe_allow_html=True)

    st.info(
        "The teaching rule: every time MedForge creates something new, ask whether it is "
        "SOURCE, DERIVED, or ILLUSTRATIVE. That label should never disappear downstream."
    )

with sandbox:
    st.subheader("Synthetic 3D volume sandbox")
    st.caption("This contains no patient data. It exists so you can see exactly how one 3D array becomes three viewing planes.")
    v = phantom_volume()
    c1,c2,c3 = st.columns(3)
    z = c1.slider("Z / axial", 0, v.shape[0]-1, v.shape[0]//2)
    y = c2.slider("Y / coronal", 0, v.shape[1]-1, v.shape[1]//2)
    x = c3.slider("X / sagittal", 0, v.shape[2]-1, v.shape[2]//2)
    axial, coronal, sagittal = med_volume.mpr_slices(v,z,y,x)
    p1,p2,p3 = st.columns(3)
    p1.image(med_volume.window_to_pil(axial), caption="Axial: volume[Z, :, :]", use_container_width=True)
    p2.image(med_volume.window_to_pil(coronal), caption="Coronal: volume[:, Y, :]", use_container_width=True)
    p3.image(med_volume.window_to_pil(sagittal), caption="Sagittal: volume[:, :, X]", use_container_width=True)

    percentile = st.slider("Try the non-clinical mask pipeline", 50, 99, 85)
    mask = med_segmentation.percentile_mask(v, percentile)
    m1,m2 = st.columns(2)
    m1.image(med_volume.window_to_pil(mask[z].astype(np.float32)), caption="Boolean mask viewed as an image", use_container_width=True)
    m2.json(med_segmentation.summarize_mask(mask).to_dict())
    st.warning("This mask is intentionally meaningless anatomically. It demonstrates data flow without pretending thresholding found a body structure.")

with lessons_tab:
    lesson = LESSONS[selected_idx]
    st.markdown(f'<div class="lab-kicker">LESSON {lesson["id"]}</div>', unsafe_allow_html=True)
    st.header(lesson["title"])
    st.write(lesson["plain"])

    q1,q2 = st.columns(2)
    q1.markdown("**Input**")
    q1.write(lesson["input"])
    q2.markdown("**Output**")
    q2.write(lesson["output"])

    st.markdown("**Why this matters**")
    st.write(lesson["why"])

    f1,f2 = st.columns(2)
    with f1:
        st.markdown(f'<div class="fail"><b>When it goes wrong</b><br>{lesson["failure"]}</div>', unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div class="fix"><b>How we repair it</b><br>{lesson["fix"]}</div>', unsafe_allow_html=True)

    st.markdown("**How we check it**")
    st.write(lesson["check"])

    module = MODULES[lesson["module"]]
    obj = getattr(module, lesson["function"])
    try:
        source = inspect.getsource(obj)
    except Exception as exc:
        source = f"# Source could not be loaded: {exc}"

    with st.expander(f'Actual MedForge code · {lesson["module"]}.{lesson["function"]}', expanded=(mode=="Technical")):
        st.code(source, language="python")
        if mode == "Beginner":
            st.caption("You do not need to memorize this. Match the function name to the plain-English step above.")

    nav1,nav2 = st.columns(2)
    if nav1.button("← Previous lesson", disabled=selected_idx==0, use_container_width=True):
        st.session_state["lesson_redirect"] = max(0, selected_idx-1)
        st.info("Use the lesson selector at left to move to the previous step.")
    if nav2.button("Next lesson →", disabled=selected_idx==len(LESSONS)-1, use_container_width=True):
        st.info("Use the lesson selector at left to move to the next step.")

with tests_tab:
    st.subheader("How we test before deployment")
    st.write(
        "MedForge has two levels of testing: deterministic unit tests for the software rules, "
        "and a public-imaging smoke suite that downloads de-identified/research datasets and pushes them through the ingestion pipeline."
    )
    st.markdown(
        """
**Current test families**
- Standard PNG image ingestion.
- Public CT and MR DICOM ingestion from pydicom examples.
- MedMNIST 2D public biomedical images.
- Synthetic multi-slice DICOM geometry with fake patient identifiers to confirm those fields do not leak into safe summaries.
- ZIP expansion, series grouping, 3D assembly, spacing, and MPR output shapes.
- Evidence-lane / mechanism-manifest rules.
- External-archive availability is reported separately so a remote server outage is not mislabeled as a MedForge failure.
        """
    )
    st.code(
        "python -m unittest discover -s tests -v\npython scripts/medforge_public_smoke.py",
        language="bash",
    )
    st.caption("The CI version runs these checks on the feature branch before deployment.")

st.caption("MedForge Build Lab · learning companion to MedForge Imaging Studio")
