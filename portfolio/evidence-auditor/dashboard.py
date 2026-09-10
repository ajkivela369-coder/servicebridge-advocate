from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor import audit_text

st.set_page_config(
    page_title="Evidence Auditor",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1450px;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
    .ea-hero {
        padding: 1.45rem 1.6rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(65,105,225,.10), rgba(128,0,128,.06));
        margin-bottom: 1.1rem;
    }
    .ea-eyebrow {font-size:.77rem; font-weight:700; letter-spacing:.11em; text-transform:uppercase; opacity:.65;}
    .ea-title {font-size:2.05rem; font-weight:760; line-height:1.1; margin:.25rem 0 .45rem;}
    .ea-subtitle {font-size:1rem; opacity:.76; max-width:900px; line-height:1.55;}
    .ea-card {
        border: 1px solid rgba(128,128,128,.20);
        border-radius: 14px;
        padding: 1rem 1.05rem;
        background: rgba(128,128,128,.035);
        min-height: 112px;
    }
    .ea-kicker {font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; opacity:.58; font-weight:700;}
    .ea-big {font-size:1.65rem; font-weight:750; margin-top:.18rem;}
    .ea-good {border-left:4px solid #2e9d64;}
    .ea-bad {border-left:4px solid #d95c5c;}
    .ea-mixed {border-left:4px solid #d79b31;}
    .ea-neutral {border-left:4px solid #7c8798;}
    .ea-missing {border-left:4px solid #8a63d2;}
    .ea-passage {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 12px;
        padding: .85rem 1rem;
        margin: .4rem 0 .8rem;
        background: rgba(128,128,128,.03);
    }
    .ea-chip {
        display:inline-block; padding:.18rem .48rem; border-radius:999px;
        background:rgba(100,100,100,.10); margin-right:.28rem; margin-bottom:.25rem;
        font-size:.76rem; font-weight:600;
    }
    .ea-footer {opacity:.62; font-size:.82rem; margin-top:1.4rem;}
    div[data-testid="stMetric"] {
        border:1px solid rgba(128,128,128,.16); border-radius:12px; padding:.7rem .8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

sample = (
    "The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
    "A later administrative review stated there was no evidence linking the current symptoms to service. "
    "A witness statement reported continuity of symptoms after training. "
    "The record may be incomplete because several service records were unavailable."
)

with st.sidebar:
    st.markdown("### Review controls")
    st.caption("Filter the evidence workspace without changing the underlying audit.")
    stance_filter = st.multiselect(
        "Evidence stance",
        ["favorable", "unfavorable", "mixed", "neutral"],
        default=["favorable", "unfavorable", "mixed", "neutral"],
    )
    min_confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05)
    st.divider()
    st.markdown("**Workflow**")
    st.caption("1. Paste synthetic or de-identified evidence\n\n2. Review issue mapping\n\n3. Inspect tensions\n\n4. Export reviewer JSON")
    st.divider()
    st.caption("Portfolio demo · Human review required")

st.markdown(
    """
    <div class="ea-hero">
      <div class="ea-eyebrow">Human-in-the-loop document intelligence</div>
      <div class="ea-title">Evidence Auditor</div>
      <div class="ea-subtitle">Turn dense case evidence into an auditable review workspace: stance classification, issue mapping, source typing, missing-record signals, contradiction pairing, and reviewer-ready structured output.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

input_col, guide_col = st.columns([2.35, 1], gap="large")
with input_col:
    text = st.text_area(
        "Evidence workspace",
        value=sample,
        height=245,
        help="Use synthetic or thoroughly de-identified content for public demonstrations.",
    )
with guide_col:
    st.markdown("#### What this demo looks for")
    st.markdown(
        """
        <div class="ea-card">
        <span class="ea-chip">stance</span><span class="ea-chip">source type</span><span class="ea-chip">issue</span><span class="ea-chip">confidence</span><br><br>
        <span class="ea-chip">missing records</span><span class="ea-chip">contradictions</span><span class="ea-chip">review routing</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("The deterministic baseline is intentionally inspectable. It does not make legal or benefits decisions.")

result = audit_text(text)
summary = result["summary"]

st.markdown("### Case snapshot")
metric_cols = st.columns(5, gap="small")
card_data = [
    ("Favorable", summary["favorable"], "ea-good"),
    ("Unfavorable", summary["unfavorable"], "ea-bad"),
    ("Mixed", summary["mixed"], "ea-mixed"),
    ("Neutral", summary["neutral"], "ea-neutral"),
    ("Missing-record flags", len(result["missing_record_flags"]), "ea-missing"),
]
for col, (label, value, klass) in zip(metric_cols, card_data):
    with col:
        st.markdown(
            f'<div class="ea-card {klass}"><div class="ea-kicker">{label}</div><div class="ea-big">{value}</div></div>',
            unsafe_allow_html=True,
        )

visible_items = [
    item for item in result["items"]
    if item["stance"] in stance_filter and item["confidence"] >= min_confidence
]

st.markdown("### Analyst workspace")
tab1, tab2, tab3, tab4 = st.tabs([
    "Evidence review",
    "Issue map",
    "Contradiction desk",
    "Export / JSON",
])

with tab1:
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        if not visible_items:
            st.info("No passages match the current filters.")
        for idx, item in enumerate(visible_items, 1):
            stance = item["stance"].upper()
            with st.expander(
                f"{idx:02d}  ·  {stance}  ·  {item['source_type'].title()}  ·  {item['confidence']:.0%}",
                expanded=item["stance"] in {"favorable", "unfavorable", "mixed"},
            ):
                st.markdown(f'<div class="ea-passage">{item["text"]}</div>', unsafe_allow_html=True)
                st.markdown("**Mapped issues**")
                st.write(" · ".join(issue.replace("_", " ").title() for issue in item["issues"]))
                st.markdown("**Detection rationale**")
                for reason in item["rationale"]:
                    st.write(f"• {reason}")
    with right:
        st.markdown("#### Review queue")
        st.metric("Visible passages", len(visible_items))
        st.metric("Potential tensions", len(result["potential_contradictions"]))
        st.metric("Issue groups", len(result["issue_summary"]))
        if result["missing_record_flags"]:
            st.markdown("#### Missing / incomplete record signals")
            for passage in result["missing_record_flags"]:
                st.warning(passage)

with tab2:
    chart_col, matrix_col = st.columns([1, 2], gap="large")
    with chart_col:
        st.markdown("#### Issue coverage")
        if result["issue_summary"]:
            st.bar_chart(result["issue_summary"], horizontal=True)
        else:
            st.info("No issue categories detected.")
    with matrix_col:
        st.markdown("#### Evidence matrix")
        st.dataframe(
            result["evidence_matrix"],
            use_container_width=True,
            hide_index=True,
            column_order=["stance", "source_type", "issues", "confidence", "passage"],
        )

with tab3:
    st.markdown("#### Same-issue opposing evidence")
    st.caption("These are candidate tensions for human reconciliation—not automatic contradictions.")
    if result["potential_contradictions"]:
        for n, finding in enumerate(result["potential_contradictions"], 1):
            st.markdown(f"**Tension {n} · {', '.join(i.replace('_', ' ').title() for i in finding['issues'])}**")
            fav_col, unfav_col = st.columns(2, gap="large")
            with fav_col:
                st.success("Favorable passage")
                st.write(finding["favorable_passage"])
            with unfav_col:
                st.error("Unfavorable passage")
                st.write(finding["unfavorable_passage"])
            st.caption(finding["note"])
            st.divider()
    else:
        st.success("No same-issue cross-stance tension detected in the current text.")

with tab4:
    export_col, json_col = st.columns([1, 2], gap="large")
    with export_col:
        st.markdown("#### Reviewer package")
        st.write("Export the complete machine-readable audit for downstream QA or human review.")
        st.download_button(
            "Download audit JSON",
            json.dumps(result, indent=2),
            file_name="evidence_audit.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption("Includes evidence items, issue tags, confidence, tension candidates, and missing-record flags.")
    with json_col:
        st.markdown("#### Structured output")
        st.json(result, expanded=False)

st.markdown(
    '<div class="ea-footer">Evidence Auditor is a portfolio/research demonstration using synthetic or de-identified examples. It is not legal advice, not a benefits decision engine, and not a substitute for source verification or human review.</div>',
    unsafe_allow_html=True,
)
