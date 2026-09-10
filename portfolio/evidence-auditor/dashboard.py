from __future__ import annotations

import json
import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor import audit_text

st.set_page_config(page_title="Evidence Auditor", page_icon="📚", layout="wide")
st.title("Evidence Auditor — Case Evidence Intelligence")
st.caption("Privacy-safe evidence extraction, issue mapping, stance review, missing-record detection, contradiction pairing, and human-review routing.")

sample = (
    "The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
    "A later administrative review stated there was no evidence linking the current symptoms to service. "
    "A witness statement reported continuity of symptoms after training. "
    "The record may be incomplete because several service records were unavailable."
)
text = st.text_area("Case evidence text", value=sample, height=220)
result = audit_text(text)
summary = result["summary"]

cols = st.columns(5)
for col, label, value in zip(cols, ["Favorable", "Unfavorable", "Mixed", "Neutral", "Missing-record flags"], [summary["favorable"], summary["unfavorable"], summary["mixed"], summary["neutral"], len(result["missing_record_flags"])]):
    col.metric(label, value)

tab1, tab2, tab3, tab4 = st.tabs(["Evidence Review", "Issue Matrix", "Contradictions", "Reviewer JSON"])

with tab1:
    stance_filter = st.multiselect("Show stance", ["favorable", "unfavorable", "mixed", "neutral"], default=["favorable", "unfavorable", "mixed", "neutral"])
    for idx, item in enumerate(result["items"], 1):
        if item["stance"] not in stance_filter:
            continue
        with st.expander(f"{idx}. {item['stance'].upper()} · {item['source_type']} · {item['confidence']:.0%}", expanded=item["stance"] in {"favorable", "unfavorable", "mixed"}):
            st.write(item["text"])
            st.write("**Issues:**", ", ".join(item["issues"]))
            st.write("**Why it was flagged**")
            for reason in item["rationale"]: st.write(f"- {reason}")
    if result["missing_record_flags"]:
        st.subheader("Missing / incomplete record signals")
        for passage in result["missing_record_flags"]: st.warning(passage)

with tab2:
    st.subheader("Issue coverage")
    if result["issue_summary"]:
        st.bar_chart(result["issue_summary"])
    st.subheader("Evidence matrix")
    st.dataframe(result["evidence_matrix"], use_container_width=True, hide_index=True)

with tab3:
    if result["potential_contradictions"]:
        for finding in result["potential_contradictions"]:
            st.warning(f"Potential tension: {', '.join(finding['issues'])}")
            left, right = st.columns(2)
            with left:
                st.write("**Favorable passage**")
                st.write(finding["favorable_passage"])
            with right:
                st.write("**Unfavorable passage**")
                st.write(finding["unfavorable_passage"])
            st.caption(finding["note"])
    else:
        st.success("No deterministic same-issue cross-stance tension detected.")

with tab4:
    st.json(result)
    st.download_button("Download audit JSON", json.dumps(result, indent=2), file_name="evidence_audit.json", mime="application/json")

st.divider()
st.caption("Portfolio/research demonstration only. Uses synthetic or de-identified examples. Not legal advice, not a benefits decision engine, and not a substitute for human review.")
