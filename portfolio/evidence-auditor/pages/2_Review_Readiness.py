from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
from page_copilot import render_page_copilot
from readiness import assess_provenance_readiness

st.set_page_config(page_title="Review Readiness · Evidence Auditor Pro", page_icon="🧭", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1.35rem;max-width:1420px}
.rr-hero{padding:1.35rem 1.5rem;border-radius:22px;background:linear-gradient(135deg,#172554,#1e3a5f);color:white;margin-bottom:1rem;box-shadow:0 16px 44px rgba(0,0,0,.14)}
.rr-title{font-size:2rem;font-weight:800;margin:.15rem 0 .4rem}.rr-sub{opacity:.82;max-width:900px;line-height:1.5}
.rr-card{border:1px solid rgba(120,130,150,.18);border-radius:16px;padding:1rem;background:rgba(120,130,150,.035)}
.rr-k{font-size:.7rem;text-transform:uppercase;letter-spacing:.09em;opacity:.58;font-weight:800}.rr-v{font-size:1.6rem;font-weight:800;margin-top:.15rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="rr-hero"><div class="rr-title">Review Readiness</div>
<div class="rr-sub">Check whether source material is actually locatable enough for a reviewer to trust the packet workflow. This page scores source naming, page locators, and usable extracted text. It does not score legal merit or medical truth.</div></div>""", unsafe_allow_html=True)

uploads = st.file_uploader("Add PDFs for provenance review", type=["pdf"], accept_multiple_files=True)
sources=[]
file_rows=[]
for uploaded in uploads or []:
    raw=uploaded.getvalue()
    digest=hashlib.sha256(raw).hexdigest()[:12]
    try:
        reader=PdfReader(uploaded)
        text_pages=0
        for page_no,page in enumerate(reader.pages,1):
            text=(page.extract_text() or "").strip()
            if text:
                text_pages+=1
            sources.append({"source_name":uploaded.name,"page":page_no,"text":text})
        file_rows.append({"file":uploaded.name,"pages":len(reader.pages),"text_pages":text_pages,"session_hash":digest})
    except Exception as exc:
        file_rows.append({"file":uploaded.name,"pages":"—","text_pages":"—","session_hash":digest,"error":str(exc)})

readiness=assess_provenance_readiness(sources)

c1,c2,c3,c4=st.columns(4,gap="small")
for col,(label,value) in zip([c1,c2,c3,c4],[
    ("Readiness",f"{readiness['score']}%"),
    ("Named sources",f"{readiness['named_source_pct']}%"),
    ("Page locators",f"{readiness['page_locator_pct']}%"),
    ("Usable text",f"{readiness['usable_text_pct']}%")]):
    with col: st.markdown(f'<div class="rr-card"><div class="rr-k">{label}</div><div class="rr-v">{value}</div></div>',unsafe_allow_html=True)

st.markdown("#### Provenance grade")
st.progress(readiness["score"] / 100 if readiness["score"] else 0)
st.markdown(f"**{readiness['grade']}**")
for flag in readiness["flags"]:
    if readiness["score"] >= 90: st.success(flag)
    elif readiness["score"] >= 75: st.warning(flag)
    else: st.info(flag)

left,right=st.columns([1.4,1],gap="large")
with left:
    st.markdown("#### Source inventory")
    if file_rows: st.dataframe(file_rows,use_container_width=True,hide_index=True)
    else: st.caption("Upload fictional or de-identified PDFs to inspect their provenance readiness.")
with right:
    st.markdown("#### Reviewer rule")
    st.markdown("""<div class="rr-card"><b>Do not confuse extraction with verification.</b><br><br>
    A packet becomes easier to audit when every passage can be traced back to a named source and page. Image-only pages with no extractable text should be routed to OCR or manual review rather than silently treated as empty evidence.</div>""",unsafe_allow_html=True)

st.caption("Session hashes are short SHA-256 fingerprints shown only to help distinguish uploaded files during review; they are not uploaded by this app page.")

render_page_copilot(sources=sources or None)
