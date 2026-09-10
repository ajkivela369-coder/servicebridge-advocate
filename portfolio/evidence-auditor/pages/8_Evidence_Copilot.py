from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from auditor import audit_sources
from floating_assistant import render_copilot_workspace

st.set_page_config(page_title="Evidence Copilot · Evidence Auditor Pro", page_icon="✦", layout="wide")

st.markdown(
    """
    <style>
    .block-container{padding-top:1.1rem;max-width:1450px}
    .copilot-hero{padding:1.45rem 1.55rem;border-radius:24px;color:white;background:
      radial-gradient(circle at 83% 8%,rgba(45,212,191,.28),transparent 30%),
      radial-gradient(circle at 12% 12%,rgba(59,130,246,.32),transparent 32%),
      linear-gradient(135deg,#0f172a,#172554 56%,#134e4a);box-shadow:0 20px 55px rgba(0,0,0,.18);margin-bottom:1.1rem}
    .copilot-kicker{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;opacity:.7}
    .copilot-title{font-size:2.15rem;font-weight:850;letter-spacing:-.02em;margin:.2rem 0 .35rem}
    .copilot-copy{max-width:920px;line-height:1.55;opacity:.86}
    .copilot-pill{display:inline-flex;align-items:center;gap:.38rem;padding:.3rem .58rem;border-radius:999px;background:rgba(255,255,255,.10);font-size:.75rem;font-weight:750;margin-top:.7rem}
    .copilot-dot{width:7px;height:7px;border-radius:50%;background:#5eead4;box-shadow:0 0 10px #5eead4}
    .copilot-card{border:1px solid rgba(100,116,139,.22);border-radius:17px;padding:1rem;background:rgba(100,116,139,.035)}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="copilot-hero">
      <div class="copilot-kicker">Evidence Auditor Pro · interactive support</div>
      <div class="copilot-title">Evidence Copilot</div>
      <div class="copilot-copy">A fast, source-grounded support workspace for questions while you review the record. Copilot stays close to the evidence, keeps source/page locators attached, surfaces gaps and tensions, and explicitly declines questions it cannot ground instead of guessing.</div>
      <div class="copilot-pill"><span class="copilot-dot"></span> Session-local · citation-first · human review required</div>
    </div>
    """,
    unsafe_allow_html=True,
)

sources = st.session_state.get("ea_sources") or []
result = st.session_state.get("ea_result") or {}

with st.expander("Load a public-safe record directly into Copilot", expanded=not bool(sources and result)):
    st.caption("Use fictional or thoroughly de-identified material in the public demo. Sensitive records should only be used in an appropriately controlled deployment.")
    uploads = st.file_uploader(
        "Source PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="copilot_page_loader",
    )
    if uploads:
        direct_sources = []
        for uploaded in uploads:
            try:
                uploaded.seek(0)
                reader = PdfReader(uploaded)
                for page_no, page in enumerate(reader.pages, 1):
                    text = (page.extract_text() or "").strip()
                    if text:
                        direct_sources.append({"source_name": uploaded.name, "page": page_no, "text": text})
            except Exception as exc:
                st.warning(f"Could not read {uploaded.name}: {exc}")
        if direct_sources:
            sources = direct_sources
            result = audit_sources(sources)
            st.session_state["ea_sources"] = sources
            st.session_state["ea_result"] = result
            st.success(f"Loaded {len(uploads)} PDF(s) across {len(sources)} text-bearing pages.")

if not sources or not result:
    demo_text = (
        "The clinician documented objective functional limitation during the fictional training event. "
        "A later administrative review stated that additional records were needed before a conclusion could be reached. "
        "A fictional witness reported continuity of symptoms after training. "
        "Several fictional service records were unavailable for review."
    )
    sources = [{"source_name": "Synthetic Copilot demo", "page": 1, "text": demo_text}]
    result = audit_sources(sources)
    st.info("Copilot is using a fictional demo record. Open Evidence Auditor Pro first or load public-safe PDFs above to work with another record.")

left, right = st.columns([2.2, 1], gap="large")
with right:
    st.markdown("### What Copilot is for")
    st.markdown(
        """
        <div class="copilot-card"><b>Fast support while reviewing</b><br><br>
        Ask what the record says about an issue, which source-backed passages are strongest, where the record appears incomplete, or which supporting and adverse passages should be reconciled.<br><br>
        <b>Not a merits engine.</b> Copilot does not decide service connection, disability status, diagnosis, rating, causation, entitlement, or legal sufficiency.</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Current workspace")
    st.metric("Evidence passages", len(result.get("items", [])))
    st.metric("Source/page units", result.get("source_count", 0))
    st.metric("Gap signals", len(result.get("missing_record_flags", [])))
    st.metric("Tension candidates", len(result.get("potential_contradictions", [])))
    st.page_link("pages/6_Elias_Assistant.py", label="Open Elias instead →", use_container_width=True)

with left:
    render_copilot_workspace(result, sources)

st.divider()
st.caption(
    "Evidence Copilot is a reviewer support tool. Answers are limited to the currently loaded audit and retain the same public-demo privacy boundary as Evidence Auditor Pro."
)
