from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from source_inventory import build_source_inventory
from page_copilot import render_page_copilot

st.set_page_config(page_title="Source Inventory · Evidence Auditor Pro", page_icon="🗂️", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:3rem}
.inv-hero{padding:1.4rem 1.55rem;border-radius:22px;color:white;background:
radial-gradient(circle at 82% 10%,rgba(45,212,191,.22),transparent 30%),
linear-gradient(135deg,#111827,#1e3a5f 62%,#134e4a);margin-bottom:1rem;box-shadow:0 18px 48px rgba(0,0,0,.16)}
.inv-title{font-size:2rem;font-weight:820;margin:.2rem 0 .35rem}.inv-sub{max-width:930px;opacity:.84;line-height:1.55}
.inv-card{border:1px solid rgba(100,116,139,.20);border-radius:16px;padding:.9rem 1rem;background:rgba(100,116,139,.035)}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="inv-hero"><div style="font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.7">Provenance control · Evidence Auditor Pro</div>
<div class="inv-title">Source Inventory</div>
<div class="inv-sub">Reconcile each document before relying on the evidence index. Stable source IDs distinguish duplicate filenames while page-range, blank-page, and numbering-gap signals help route incomplete extraction for human review.</div></div>""", unsafe_allow_html=True)

uploads = st.file_uploader("Source PDFs", type=["pdf"], accept_multiple_files=True, help="Use fictional or thoroughly de-identified records in public demos.")

sources=[]
for uploaded in uploads or []:
    try:
        uploaded.seek(0)
        reader=PdfReader(uploaded)
        for page_no,page in enumerate(reader.pages,1):
            sources.append({"source_name":uploaded.name,"page":page_no,"text":page.extract_text() or ""})
    except Exception as exc:
        st.warning(f"Could not inspect {uploaded.name}: {exc}")

if not sources:
    sources=[
        {"source_name":"fictional_exam.pdf","page":1,"text":"Synthetic page one."},
        {"source_name":"fictional_exam.pdf","page":2,"text":""},
        {"source_name":"fictional_exam.pdf","page":3,"text":"Synthetic page three."},
    ]
    st.info("Showing a fictional demonstration inventory until PDFs are loaded.")

report=build_source_inventory(sources)

c1,c2,c3=st.columns(3,gap="small")
c1.metric("Documents",report["document_count"])
c2.metric("Need review",report["documents_needing_review"])
c3.metric("Ready",report["document_count"]-report["documents_needing_review"])

rows=[]
for doc in report["documents"]:
    rows.append({
        "Source ID":doc["source_id"],
        "File":doc["source_name"],
        "Observed pages":doc["observed_pages"],
        "Observed range":doc["page_range"],
        "Text pages":doc["text_pages"],
        "Blank / no text":doc["blank_pages"],
        "Missing numbers":doc["missing_pages"],
        "Unpaged units":doc["unpaged_units"],
        "Status":doc["status"].title(),
    })

st.markdown("### Document reconciliation")
control_a,control_b,control_c=st.columns([1.1,1.6,1],gap="small")
with control_a:
    status_filter=st.selectbox("Status",["All","Review","Ready"],index=0)
with control_b:
    file_filter=st.text_input("Filter by file or source ID",placeholder="Example: fictional_exam or SRC-")
with control_c:
    st.caption("Export the full inventory, not only the filtered view.")
    st.download_button(
        "Download inventory JSON",
        data=json.dumps(report,indent=2),
        file_name="evidence_source_inventory.json",
        mime="application/json",
        use_container_width=True,
    )

filtered_rows=rows
if status_filter != "All":
    filtered_rows=[row for row in filtered_rows if row["Status"] == status_filter]
if file_filter.strip():
    needle=file_filter.strip().lower()
    filtered_rows=[row for row in filtered_rows if needle in row["File"].lower() or needle in row["Source ID"].lower()]

st.dataframe(filtered_rows,use_container_width=True,hide_index=True)
st.caption(f"Showing {len(filtered_rows)} of {len(rows)} document(s). Filters affect only the table view; review cues and exports retain the full inventory.")

st.markdown("### Review cues")
flagged=[doc for doc in report["documents"] if doc["flags"]]
if not flagged:
    st.success("No page-range or extraction-gap cues detected in the supplied source rows.")
for doc in flagged:
    with st.expander(f"{doc['source_name']} · {doc['source_id']} · review",expanded=True):
        for flag in doc["flags"]:
            st.warning(flag)
        st.caption("Check the original document or OCR/manual extraction before treating these signals as a complete record assessment.")

st.markdown(f'<div class="inv-card"><b>Reviewer rule:</b> {report["note"]}</div>',unsafe_allow_html=True)

# Give the floating Copilot page-local text-bearing evidence when available.
render_page_copilot([row for row in sources if (row.get("text") or "").strip()])
