from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditor import audit_sources
from coverage import assess_issue_coverage
from page_copilot import render_page_copilot

st.set_page_config(page_title="Coverage Gaps · Evidence Auditor Pro", page_icon="🧭", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.3rem}
.cg-hero{padding:1.35rem 1.5rem;border-radius:22px;background:linear-gradient(135deg,#172554,#1e3a8a 58%,#0f766e);color:white;margin-bottom:1rem}
.cg-title{font-size:2rem;font-weight:800;margin:.15rem 0 .35rem}.cg-sub{opacity:.82;max-width:920px;line-height:1.5}
.cg-card{border:1px solid rgba(100,110,130,.18);border-radius:15px;padding:.9rem 1rem;background:rgba(120,130,150,.035)}
.cg-thin{border-left:4px solid #dc2626}.cg-dev{border-left:4px solid #d97706}.cg-strong{border-left:4px solid #059669}
.cg-k{font-size:.7rem;text-transform:uppercase;letter-spacing:.09em;opacity:.58;font-weight:800}.cg-v{font-size:1.55rem;font-weight:800}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="cg-hero"><div class="cg-title">Evidence Coverage Map</div>
<div class="cg-sub">Find issues that look impressive at a glance but still depend on too few passages, one source, weak source-type diversity, or missing page locators. Coverage measures review depth—not claim merit.</div></div>""", unsafe_allow_html=True)

uploads = st.file_uploader("Add source PDFs", type=["pdf"], accept_multiple_files=True)
pasted = st.text_area("Optional pasted evidence", height=130, placeholder="Use fictional or de-identified content in the public demo.")

sources=[]
if pasted.strip():
    sources.append({"source_name":"Pasted evidence","page":None,"text":pasted})
for uploaded in uploads or []:
    try:
        uploaded.seek(0)
        reader=PdfReader(uploaded)
        for page_no,page in enumerate(reader.pages,1):
            text=(page.extract_text() or "").strip()
            if text:
                sources.append({"source_name":uploaded.name,"page":page_no,"text":text})
    except Exception as exc:
        st.warning(f"Could not read {uploaded.name}: {exc}")

if not sources:
    sources=[{
        "source_name":"synthetic_exam.pdf","page":2,
        "text":"The clinician documented objective functional limitation after training. The condition was aggravated during duty."
    },{
        "source_name":"synthetic_review.pdf","page":5,
        "text":"The administrative review stated there was no evidence linking the current symptoms to service."
    }]
    st.caption("Showing a fictional built-in example until you add evidence.")

result=audit_sources(sources)
coverage=assess_issue_coverage(result["items"])

m1,m2,m3,m4=st.columns(4)
for col,label,value,klass in [
    (m1,"Issues",coverage["issue_count"],""),(m2,"Strong",coverage["strong"],"cg-strong"),
    (m3,"Developing",coverage["developing"],"cg-dev"),(m4,"Thin",coverage["thin"],"cg-thin")]:
    with col:
        st.markdown(f'<div class="cg-card {klass}"><div class="cg-k">{label}</div><div class="cg-v">{value}</div></div>',unsafe_allow_html=True)

st.markdown("### Priority review gaps")
if not coverage["priority_gaps"]:
    st.success("No coverage-gap flags were generated for the current evidence set.")
for item in coverage["priority_gaps"]:
    band=item["coverage_band"].title()
    with st.expander(f"{item['issue'].replace('_',' ').title()} · {band} · {item['coverage_score']}/100", expanded=item["coverage_band"]=="thin"):
        a,b,c,d=st.columns(4)
        a.metric("Passages",item["passages"]); b.metric("Named sources",item["named_sources"])
        c.metric("Source types",len(item["source_types"])); d.metric("Page locators",item["page_locators"])
        st.write("**Source types:** "+(", ".join(x.title() for x in item["source_types"]) or "None detected"))
        for flag in item["flags"]:
            st.warning(flag)

st.markdown("### Coverage matrix")
rows=[]
for i in coverage["issues"]:
    rows.append({
        "Issue":i["issue"].replace("_"," ").title(),"Score":i["coverage_score"],"Band":i["coverage_band"].title(),
        "Passages":i["passages"],"Named sources":i["named_sources"],"Source types":len(i["source_types"]),
        "Page locators":i["page_locators"],"Favorable":i["favorable"],"Unfavorable":i["unfavorable"],"Mixed":i["mixed"]
    })
st.dataframe(rows,use_container_width=True,hide_index=True)
st.caption(coverage["note"])

render_page_copilot(sources=sources, result=result)
