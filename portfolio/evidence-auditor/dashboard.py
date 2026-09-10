from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor import audit_sources, verify_quote
from floating_assistant import render_floating_copilot
from packet_assurance import assess_packet_assurance
from packet_builder import build_packet

st.set_page_config(page_title="Evidence Auditor Pro", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1540px}
[data-testid="stSidebar"]{border-right:1px solid rgba(120,130,150,.18)}
.hero{padding:1.6rem 1.7rem;border-radius:24px;background:
radial-gradient(circle at 15% 15%,rgba(56,132,255,.22),transparent 30%),
radial-gradient(circle at 90% 10%,rgba(24,185,160,.16),transparent 28%),
linear-gradient(135deg,#14203a,#26395d);color:white;border:1px solid rgba(255,255,255,.08);box-shadow:0 18px 55px rgba(0,0,0,.18);margin-bottom:1rem}
.eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;opacity:.72}
.title{font-size:2.35rem;font-weight:800;line-height:1.05;margin:.25rem 0 .5rem}
.subtitle{font-size:1rem;line-height:1.55;max-width:980px;opacity:.83}
.card{border:1px solid rgba(120,130,150,.20);border-radius:16px;padding:1rem;background:rgba(120,130,150,.035)}
.metric{border:1px solid rgba(120,130,150,.17);border-radius:15px;padding:.85rem 1rem;min-height:100px}
.ml{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;opacity:.58;font-weight:800}
.mv{font-size:1.65rem;font-weight:800;margin-top:.15rem}
.good{border-left:4px solid #20a66a}.bad{border-left:4px solid #d85b5b}.mix{border-left:4px solid #d89a34}.blue{border-left:4px solid #3b82f6}
.pass{border:1px solid rgba(120,130,150,.18);border-radius:12px;padding:.85rem 1rem;background:rgba(120,130,150,.03)}
.chip{display:inline-block;padding:.2rem .5rem;border-radius:999px;background:rgba(80,100,140,.10);font-size:.75rem;font-weight:700;margin:.15rem}
.preview-v{border-radius:18px;padding:1.1rem;background:linear-gradient(135deg,rgba(37,99,235,.10),rgba(16,185,129,.08));border:1px solid rgba(37,99,235,.23)}
.preview-f{border-radius:18px;padding:1.1rem;background:rgba(120,130,150,.035);border:1px solid rgba(120,130,150,.20)}
.flow{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap;margin:.7rem 0}
.step{padding:.55rem .7rem;border-radius:12px;border:1px solid rgba(80,100,140,.24);background:rgba(80,100,140,.06);font-size:.82rem;font-weight:700}
.assurance-strip{border:1px solid rgba(37,99,235,.24);border-radius:16px;padding:.9rem 1rem;background:linear-gradient(135deg,rgba(37,99,235,.06),rgba(16,185,129,.04));margin:.75rem 0}
.footer{opacity:.62;font-size:.80rem;margin-top:1.6rem}
</style>
""", unsafe_allow_html=True)

def extract_pdf_sources(uploaded):
    reader=PdfReader(uploaded)
    out=[]
    for page_no,page in enumerate(reader.pages,1):
        text=(page.extract_text() or "").strip()
        if text:
            out.append({"source_name":uploaded.name,"page":page_no,"text":text})
    return out

sample=("The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
"A later administrative review stated there was no evidence linking the current symptoms to service. "
"A witness statement reported continuity of symptoms after training. "
"The record may be incomplete because several service records were unavailable.")

with st.sidebar:
    st.markdown("### Review controls")
    st.caption("Evidence stays session-local unless you explicitly save or export it.")
    stance_filter=st.multiselect("Evidence stance",["favorable","unfavorable","mixed","neutral"],default=["favorable","unfavorable","mixed","neutral"])
    min_confidence=st.slider("Minimum confidence",0.0,1.0,0.0,0.05)
    copilot_enabled=st.toggle("Floating Evidence Copilot",value=True,help="Shows a compact assistant launcher in the lower-right corner. Elias remains a separate full workspace.")
    st.divider()
    st.markdown("**Packet defaults**")
    packet_style_label=st.radio("Style",["Visual Claim Packet","Formal Evidence Review"],index=0)
    st.divider()
    st.caption("Public demo: fictional/de-identified content only. Human verification required.")

st.markdown("""<div class="hero"><div class="eyebrow">Source-backed case intelligence · v2</div>
<div class="title">Evidence Auditor Pro</div>
<div class="subtitle">Review PDFs, preserve page provenance, verify quotations, map issues, surface opposing evidence, build rebuttal-ready comparisons, and export polished reviewer packets with screenshots, diagrams, mechanism maps, appendices, and an embedded assurance summary.</div></div>""",unsafe_allow_html=True)

left,right=st.columns([1.55,1],gap="large")
with left:
    uploaded_pdfs=st.file_uploader("Add source PDFs",type=["pdf"],accept_multiple_files=True)
    pasted_text=st.text_area("Paste evidence or notes",value=sample,height=180)
with right:
    uploaded_images=st.file_uploader("Add screenshots / diagrams",type=["png","jpg","jpeg"],accept_multiple_files=True)
    st.markdown("""<div class="card"><span class="chip">page provenance</span><span class="chip">quote check</span>
    <span class="chip">issue map</span><span class="chip">rebuttal desk</span><span class="chip">mechanism map</span>
    <span class="chip">visual exhibits</span><span class="chip">assurance summary</span><span class="chip">PDF packet</span><br><br>
    <b>Public-safe by design:</b> the repository ships fictional examples only.</div>""",unsafe_allow_html=True)
    if uploaded_images:
        cols=st.columns(min(3,len(uploaded_images)))
        for i,img in enumerate(uploaded_images[:3]):
            with cols[i]: st.image(img,use_container_width=True)

sources=[]
if pasted_text.strip(): sources.append({"source_name":"Pasted evidence","page":None,"text":pasted_text})
for uploaded in uploaded_pdfs or []:
    try:
        uploaded.seek(0); sources.extend(extract_pdf_sources(uploaded))
    except Exception as exc:
        st.warning(f"Could not extract {uploaded.name}: {exc}")

result=audit_sources(sources)
st.session_state["ea_sources"]=sources
st.session_state["ea_result"]=result
summary=result["summary"]
metrics=st.columns(6,gap="small")
for col,(label,value,klass) in zip(metrics,[
    ("Favorable",summary["favorable"],"good"),("Unfavorable",summary["unfavorable"],"bad"),
    ("Mixed",summary["mixed"],"mix"),("Sources/pages",result["source_count"],"blue"),
    ("Tensions",len(result["potential_contradictions"]),"mix"),
    ("Record gaps",len(result["missing_record_flags"]),"blue")]):
    with col: st.markdown(f'<div class="metric {klass}"><div class="ml">{label}</div><div class="mv">{value}</div></div>',unsafe_allow_html=True)

tabs=st.tabs(["Command Center","Evidence Review","Quote Check","Rebuttal Lab","Mechanism Map","Packet Studio"])

with tabs[0]:
    a,b=st.columns([1,1],gap="large")
    with a:
        st.markdown("#### Issue heat map")
        if result["issue_summary"]: st.bar_chart(result["issue_summary"],horizontal=True)
        else: st.info("Add evidence to populate the issue map.")
    with b:
        st.markdown("#### Review routing")
        st.markdown(f"""<div class="card"><span class="chip">{len(result['items'])} passages</span>
        <span class="chip">{len(result['issue_summary'])} issue groups</span>
        <span class="chip">{len(result['potential_contradictions'])} tensions</span>
        <span class="chip">{len(result['missing_record_flags'])} gap signals</span>
        <div class="flow"><span class="step">Verify source</span>→<span class="step">Confirm quote</span>→
        <span class="step">Resolve tension</span>→<span class="step">Build packet</span></div></div>""",unsafe_allow_html=True)
        for flag in result["missing_record_flags"][:5]:
            loc=flag["source_name"]+(f", p. {flag['page']}" if flag["page"] else "")
            st.warning(f"{loc}: {flag['text']}")

with tabs[1]:
    visible=[i for i in result["items"] if i["stance"] in stance_filter and i["confidence"]>=min_confidence]
    st.caption("Every extracted passage retains source name and PDF page when available.")
    for item in visible:
        loc=item["source_name"]+(f" · p. {item['page']}" if item["page"] else "")
        with st.expander(f"{item['evidence_id']} · {item['stance'].upper()} · {item['confidence']:.0%} · {loc}",expanded=item["stance"] in {"favorable","unfavorable","mixed"}):
            st.markdown(f'<div class="pass">{item["text"]}</div>',unsafe_allow_html=True)
            st.write("**Issues:** "+" · ".join(x.replace("_"," ").title() for x in item["issues"]))
            st.write("**Source type:** "+item["source_type"].title())
            for reason in item["rationale"]: st.caption(reason)

with tabs[2]:
    st.markdown("#### Source quote verifier")
    quote=st.text_area("Paste the exact quotation you intend to use",height=120)
    check=verify_quote(quote,sources)
    if quote.strip():
        if check["status"]=="verified":
            st.success(check["note"])
            for match in check["matches"]:
                loc=match["source_name"]+(f", p. {match['page']}" if match["page"] else "")
                st.write(f"Verified against **{loc}**")
        else: st.error(check["note"])
    st.caption("Text match ≠ medical or legal truth. Verify the source and context before external use.")

with tabs[3]:
    st.markdown("#### Same-issue opposing evidence")
    st.caption("Candidate tensions for human reconciliation, not automatic findings of error.")
    if not result["potential_contradictions"]: st.success("No same-issue cross-stance tension detected.")
    for n,t in enumerate(result["potential_contradictions"][:12],1):
        st.markdown(f"**Tension {n} · {', '.join(x.replace('_',' ').title() for x in t['issues'])}**")
        c1,c2=st.columns(2,gap="large")
        with c1:
            st.success("Supporting / favorable"); st.write(t["favorable"]["text"])
            st.caption(t["favorable"]["source_name"]+(f" · p. {t['favorable']['page']}" if t["favorable"]["page"] else ""))
        with c2:
            st.error("Adverse / opposing"); st.write(t["unfavorable"]["text"])
            st.caption(t["unfavorable"]["source_name"]+(f" · p. {t['unfavorable']['page']}" if t["unfavorable"]["page"] else ""))
        st.divider()

with tabs[4]:
    st.markdown("#### Reviewer-supplied mechanism / sequence")
    default=["Documented event / exposure / injury","Anatomical or functional change supported by the record",
             "Observed symptoms or objective findings","Repeated aggravation / persistence","Current functional impact"]
    mechanism_text=st.text_area("One step per line",value="\n".join(default),height=180)
    mechanism_steps=[x.strip(" -•\t") for x in mechanism_text.splitlines() if x.strip()]
    st.markdown('<div class="flow">'+'→'.join(f'<span class="step">{x}</span>' for x in mechanism_steps)+'</div>',unsafe_allow_html=True)
    st.info("Mechanism maps are reviewer-authored explanatory aids; the app does not silently invent medical causation.")

with tabs[5]:
    st.markdown("#### Packet Studio")
    style=st.radio("Document style",["Visual Claim Packet","Formal Evidence Review"],horizontal=True,index=0 if packet_style_label=="Visual Claim Packet" else 1)
    case_title=st.text_input("Packet title",value="Synthetic Demonstration Case — Evidence Review")
    executive_summary=st.text_area("Executive summary",value="This packet organizes source-backed evidence, issue coverage, record gaps, opposing evidence, reviewer-supplied mechanism steps, and visual exhibits for human review.",height=110)
    rebuttal_note=st.text_area("Reviewer rebuttal note",placeholder="Example: The adverse review did not address the source passage documenting...",height=90)
    proposed_quotes_text=st.text_area(
        "Proposed verbatim quotations for packet verification",
        placeholder="One quotation per line. Exact source matches can be listed in the exported assurance register.",
        height=95,
        help="Unresolved lines remain explicitly marked as unresolved; fuzzy similarity is never promoted to a verified quote.",
    )
    proposed_quotes=[line.strip() for line in proposed_quotes_text.splitlines() if line.strip()]
    assurance=assess_packet_assurance(result.get("items",[]),sources,proposed_quotes)

    st.markdown(
        f'<div class="assurance-strip"><b>Packet Assurance {assurance["score"]}/100</b> · '
        f'{assurance["band"].replace("_"," ").title()} · Provenance {assurance["provenance_score"]} · '
        f'Coverage {assurance["coverage_score"]} · Quote integrity {assurance["quote_score"]}</div>',
        unsafe_allow_html=True,
    )
    if assurance["blockers"]:
        st.warning("Reviewer blockers remain: " + " ".join(assurance["blockers"]))
    else:
        st.success("No assurance blockers detected by this screening pass. Human source review is still required.")

    p1,p2=st.columns([1.3,1],gap="large")
    with p1:
        klass="preview-v" if style=="Visual Claim Packet" else "preview-f"
        desc=("Color-forward evidence cards, assurance summary, mechanism map, screenshot exhibits, rebuttal desk, and source appendix."
              if style=="Visual Claim Packet" else
              "Restrained typography, assurance summary, issue table, source-backed passages, tension analysis, and source appendix.")
        st.markdown(f'<div class="{klass}"><h4>{style}</h4>{desc}</div>',unsafe_allow_html=True)
    with p2:
        include_images=st.checkbox("Include uploaded screenshots / diagrams",value=style=="Visual Claim Packet")
        include_assurance=st.checkbox("Embed Reviewer Assurance Summary",value=True)
        st.caption("Assurance is a workflow-quality screen, not a merits decision. Visual exhibits should be verified against originals.")
    shots=[]
    if include_images:
        for img in uploaded_images or []:
            img.seek(0); shots.append({"name":img.name,"caption":img.name,"bytes":img.read()})
    try:
        packet_style="visual_claim" if style=="Visual Claim Packet" else "formal_review"
        payload=build_packet(result,packet_style=packet_style,case_title=case_title,executive_summary=executive_summary,
                             mechanism_steps=mechanism_steps,rebuttal_note=rebuttal_note,screenshots=shots,
                             assurance=assurance if include_assurance else None)
        d1,d2=st.columns(2)
        with d1: st.download_button("Download generated PDF",payload,file_name="evidence_auditor_visual_packet.pdf" if packet_style=="visual_claim" else "evidence_auditor_formal_review.pdf",mime="application/pdf",use_container_width=True)
        export_json={"audit":result,"packet_assurance":assurance}
        with d2: st.download_button("Download reviewer JSON",json.dumps(export_json,indent=2),file_name="evidence_audit.json",mime="application/json",use_container_width=True)
        st.caption(f"Generated packet size: {len(payload)/1024:.1f} KB")
    except Exception as exc:
        st.error(f"Packet generation failed: {exc}")

render_floating_copilot(result,sources,enabled=copilot_enabled)

st.markdown('<div class="footer">Evidence Auditor Pro is a research/portfolio tool. It does not make legal, medical, disability, service-connection, or benefits determinations. Public examples are fictional; source verification and human review remain required.</div>',unsafe_allow_html=True)
