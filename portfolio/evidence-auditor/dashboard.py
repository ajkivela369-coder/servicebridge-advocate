from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor import audit_text

st.set_page_config(page_title="Evidence Auditor", page_icon="📚", layout="wide")
st.title("Evidence Auditor — Benefits & Disability Case Review")
st.caption(
    "A privacy-safe portfolio demo for evidence extraction, stance classification, source typing, contradiction spotting, and human review."
)

sample = (
    "The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
    "A later administrative review stated there was no evidence linking the current symptoms to service. "
    "A witness statement reported continuity of symptoms after training. "
    "The record may be incomplete because several service records were unavailable."
)

text = st.text_area("Case evidence text", value=sample, height=220)
result = audit_text(text)

summary = result["summary"]
cols = st.columns(4)
for col, label, key in zip(
    cols,
    ["Favorable", "Unfavorable", "Mixed", "Neutral"],
    ["favorable", "unfavorable", "mixed", "neutral"],
):
    col.metric(label, summary[key])

st.subheader("Evidence review")
stance_filter = st.multiselect(
    "Show stance",
    ["favorable", "unfavorable", "mixed", "neutral"],
    default=["favorable", "unfavorable", "mixed", "neutral"],
)

for idx, item in enumerate(result["items"], 1):
    if item["stance"] not in stance_filter:
        continue
    with st.expander(
        f"{idx}. {item['stance'].upper()} · {item['source_type']} · confidence {item['confidence']:.0%}",
        expanded=item["stance"] in {"favorable", "unfavorable", "mixed"},
    ):
        st.write(item["text"])
        st.write("**Why it was flagged**")
        for reason in item["rationale"]:
            st.write(f"- {reason}")

st.subheader("Potential contradictions / tensions")
if result["potential_contradictions"]:
    for finding in result["potential_contradictions"]:
        st.warning(finding["note"])
        st.write("Overlapping terms:", ", ".join(finding["shared_terms"]))
else:
    st.success("No deterministic cross-stance tension detected in this sample.")

st.subheader("Reviewer JSON")
st.json(result)
st.download_button(
    "Download audit JSON",
    json.dumps(result, indent=2),
    file_name="evidence_audit.json",
    mime="application/json",
)

st.divider()
st.caption(
    "Portfolio/research demonstration only. Uses synthetic or de-identified examples. Not legal advice, not a benefits decision engine, and not a substitute for human review."
)
