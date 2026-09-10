from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from packet_guard import audit_packet_quotes

st.set_page_config(page_title="Packet Integrity · Evidence Auditor Pro", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .block-container{padding-top:1.35rem;max-width:1450px}
    .guard-hero{padding:1.4rem 1.55rem;border-radius:22px;background:linear-gradient(135deg,#172554,#1e3a5f);color:white;margin-bottom:1rem}
    .guard-title{font-size:2rem;font-weight:800;margin:.2rem 0}
    .guard-sub{opacity:.82;max-width:900px;line-height:1.5}
    .guard-card{border:1px solid rgba(120,130,150,.2);border-radius:15px;padding:1rem;background:rgba(120,130,150,.035)}
    .verified{border-left:4px solid #20a66a}.partial{border-left:4px solid #d89a34}.missing{border-left:4px solid #d85b5b}
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_pdf_sources(uploaded):
    reader = PdfReader(uploaded)
    sources = []
    for page_no, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            sources.append({"source_name": uploaded.name, "page": page_no, "text": text})
    return sources


st.markdown(
    """<div class="guard-hero"><div style="font-size:.7rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;opacity:.72">Export safety · source fidelity</div>
    <div class="guard-title">Packet Integrity Gate</div>
    <div class="guard-sub">Check every proposed verbatim quotation against source-page text before it reaches a final packet. Exact matches pass; similar wording stays visibly unresolved instead of being promoted into a quote.</div></div>""",
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 1], gap="large")
with left:
    uploads = st.file_uploader("Source PDFs", type=["pdf"], accept_multiple_files=True)
    pasted = st.text_area(
        "Optional source text",
        value="The clinician documented objective functional limitation and stated that the condition was aggravated during duty.",
        height=120,
    )
with right:
    proposed = st.text_area(
        "Proposed packet quotations — one per line",
        value=(
            "The clinician documented objective functional limitation and stated that the condition was aggravated during duty.\n"
            "The clinician said the condition clearly worsened because of service."
        ),
        height=190,
    )
    st.caption("Use this for text intended to appear inside quotation marks. Paraphrases should not be entered as quotes.")

sources = []
if pasted.strip():
    sources.append({"source_name": "Pasted source", "page": None, "text": pasted})
for uploaded in uploads or []:
    try:
        uploaded.seek(0)
        sources.extend(extract_pdf_sources(uploaded))
    except Exception as exc:
        st.warning(f"Could not extract {uploaded.name}: {exc}")

quotes = [line.strip() for line in proposed.splitlines() if line.strip()]
report = audit_packet_quotes(quotes, sources)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Proposed quotes", report["quote_count"])
m2.metric("Verified", report["counts"]["verified"])
m3.metric("Similar / partial", report["counts"]["partial"])
m4.metric("Not found", report["counts"]["not_found"])

if report["export_ready"]:
    st.success("Quote integrity gate passed: every proposed verbatim quotation has an exact normalized source match.")
else:
    st.error(f"Quote integrity gate blocked: {report['unresolved']} proposed quotation(s) require correction or paraphrase before source-safe export.")

st.markdown("### Verification register")
for item in report["results"]:
    status = item["status"]
    klass = "verified" if status == "verified" else "partial" if status == "partial" else "missing"
    label = "VERIFIED" if status == "verified" else "SIMILAR — NOT VERBATIM" if status == "partial" else "NOT VERIFIED"
    st.markdown(f'<div class="guard-card {klass}"><b>{item["quote_id"]} · {label}</b><br><br>“{item["quote"]}”</div>', unsafe_allow_html=True)
    if item["matches"]:
        match = item["matches"][0]
        loc = match["source_name"] + (f", p. {match['page']}" if match.get("page") else "")
        context = match.get("context", {})
        st.caption(f"Best source: {loc} · confidence {item['confidence']:.0%}")
        if context.get("before"):
            st.write("**Before:**", context["before"])
        st.write("**Matched source wording:**", context.get("match", ""))
        if context.get("after"):
            st.write("**After:**", context["after"])
    st.caption(item["note"])
    st.divider()

st.info(report["policy"])
st.caption("This gate checks source fidelity, not authenticity, medical truth, legal relevance, or entitlement. Human review remains required.")
