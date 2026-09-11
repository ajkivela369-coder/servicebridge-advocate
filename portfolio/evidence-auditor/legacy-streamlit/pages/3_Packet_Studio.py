from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from packet_assurance import assess_packet_assurance
from packet_builder import build_packet
from page_copilot import render_page_copilot
from ui_shell import render_app_nav, workspace_status

st.set_page_config(page_title="Packet Studio · Evidence Auditor Pro", page_icon="📄", layout="wide", initial_sidebar_state="expanded")
render_app_nav("packet")

st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"]{display:none}
    .block-container{max-width:1320px;padding-top:1rem;padding-bottom:5rem}
    .hero{border:1px solid rgba(100,116,139,.18);border-radius:20px;padding:1.15rem 1.25rem;background:linear-gradient(135deg,rgba(37,99,235,.045),rgba(16,185,129,.025));margin-bottom:1rem}
    .hero h1{font-size:1.75rem;letter-spacing:-.025em;margin:0 0 .35rem}.hero p{opacity:.68;margin:0;max-width:920px;line-height:1.5}
    .assurance{border:1px solid rgba(37,99,235,.20);border-radius:16px;padding:.9rem 1rem;background:rgba(37,99,235,.035)}
    .packet-card{border:1px solid rgba(100,116,139,.18);border-radius:16px;padding:1rem;background:rgba(100,116,139,.025)}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="hero"><h1>Packet Studio</h1><p>Turn the loaded record into a reviewer-facing evidence packet. Elias and Case Review do the conversational and quality-control work; this page controls the final structure, assurance checks, visual exhibits, and export.</p></div>""",
    unsafe_allow_html=True,
)

sources, result = workspace_status()
if not sources or not result:
    st.warning("No case record is loaded in this session. Add the documents once in Elias before building a packet.")
    st.page_link("dashboard.py", label="Open Elias and add case files →", icon="💬", use_container_width=True)
    st.stop()

left, right = st.columns([1.5, 1], gap="large")
with left:
    st.markdown("### Packet setup")
    lane = st.selectbox(
        "Packet type",
        ["VA Evidence Packet", "Formal Evidence Review"],
        help="VA Evidence Packet uses the visual claim-packet layout; Formal Evidence Review uses restrained styling.",
    )
    title_default = "VA Evidence Review Packet — Draft for Human Review" if lane == "VA Evidence Packet" else "Formal Evidence Review — Draft"
    case_title = st.text_input("Packet title", value=title_default)
    executive_summary = st.text_area(
        "Executive summary",
        value=(
            "This packet organizes the loaded source record, favorable and adverse evidence, issue coverage, potential contradictions, record gaps, and page-level source locators for human review."
        ),
        height=120,
    )
    rebuttal_note = st.text_area(
        "Reviewer rebuttal / clarification note",
        placeholder="Use this for a short, source-grounded explanation of what an adverse review missed or what the record needs clarified.",
        height=105,
    )

    st.markdown("### Mechanism / sequence")
    st.caption("Use only steps you can support from the source record. This is an explanatory aid, not an automatic medical-causation finding.")
    default_steps = [
        "Documented event, exposure, injury, or onset",
        "Objective or clinical findings in the record",
        "Longitudinal persistence or repeated aggravation",
        "Current symptoms and functional limits",
        "Work / daily-function impact documented by sources",
    ]
    mechanism_text = st.text_area("One step per line", value="\n".join(default_steps), height=150)
    mechanism_steps = [line.strip(" -•\t") for line in mechanism_text.splitlines() if line.strip()]

    st.markdown("### Proposed quotations")
    proposed_quotes_text = st.text_area(
        "One proposed verbatim quotation per line",
        placeholder="Exact quotation from the record…",
        height=120,
        help="Packet Assurance will mark unresolved quotations rather than silently treating them as verified.",
    )
    proposed_quotes = [line.strip() for line in proposed_quotes_text.splitlines() if line.strip()]

    st.markdown("### Visual exhibits")
    uploaded_images = st.file_uploader(
        "Add screenshots or diagrams",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Use only material you are authorized to include. Verify labels and source context before filing.",
    )
    screenshots = []
    for image in uploaded_images or []:
        image.seek(0)
        screenshots.append({"name": image.name, "caption": image.name, "bytes": image.read()})

with right:
    st.markdown("### Reviewer assurance")
    assurance = assess_packet_assurance(result.get("items", []), sources, proposed_quotes)
    st.markdown(
        f'<div class="assurance"><b>{assurance["score"]}/100 · {assurance["band"].replace("_", " ").title()}</b><br><br>'
        f'Provenance {assurance["provenance_score"]} · Coverage {assurance["coverage_score"]} · Quote integrity {assurance["quote_score"]}</div>',
        unsafe_allow_html=True,
    )
    if assurance.get("blockers"):
        st.warning("\n\n".join(assurance["blockers"]))
    else:
        st.success("No automated assurance blockers were detected. Human review is still required.")

    st.markdown("### What will be included")
    st.markdown(
        """
        <div class="packet-card">
        <b>Core packet</b><br>
        • executive summary<br>
        • evidence / issue map<br>
        • source-locatable passages<br>
        • supporting-vs-adverse tension review<br>
        • record-gap signals<br>
        • reviewer assurance summary<br>
        • source appendix<br><br>
        <b>Optional</b><br>
        • reviewer mechanism sequence<br>
        • rebuttal / clarification note<br>
        • uploaded visual exhibits
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Export")
    packet_style = "visual_claim" if lane == "VA Evidence Packet" else "formal_review"
    try:
        payload = build_packet(
            result,
            packet_style=packet_style,
            case_title=case_title,
            executive_summary=executive_summary,
            mechanism_steps=mechanism_steps,
            rebuttal_note=rebuttal_note,
            screenshots=screenshots,
            assurance=assurance,
        )
        filename = "elias_va_evidence_packet_draft.pdf" if lane == "VA Evidence Packet" else "elias_formal_evidence_review_draft.pdf"
        st.download_button(
            "Download PDF packet draft",
            payload,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
        export_json = {
            "audit": result,
            "packet_assurance": assurance,
            "packet_type": lane,
            "title": case_title,
        }
        st.download_button(
            "Download reviewer JSON",
            json.dumps(export_json, indent=2),
            file_name="elias_packet_review.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption(f"Generated PDF size: {len(payload)/1024:.1f} KB")
    except Exception as exc:
        st.error(f"Packet generation failed: {exc}")

st.divider()
st.caption("Packet Studio creates a source-organized draft for reviewer use. It does not determine service connection, disability status, diagnosis, rating percentage, entitlement, or legal sufficiency.")

render_page_copilot()
