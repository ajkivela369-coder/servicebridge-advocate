from __future__ import annotations

import json
import streamlit as st
from healthqa import audit

st.set_page_config(page_title="HealthQA Auditor", page_icon="🩺", layout="wide")
st.title("HealthQA Auditor — Safety-First Health-Science AI QA")
st.caption("Review model-generated health content for safety signals, calibrated language, and human-review needs.")

sample = "Chest pain can have many causes. If it is severe or accompanied by difficulty breathing, seek urgent medical evaluation."
text = st.text_area("AI-generated health-science output", value=sample, height=180)
result = audit(text)

cols = st.columns(4)
cols[0].metric("Disposition", result.disposition)
cols[1].metric("Safety", f"{result.safety_score}%")
cols[2].metric("Quality", f"{result.quality_score}%")
cols[3].metric("Human review", "Yes" if result.requires_human_review else "No")

left, right = st.columns(2)
with left:
    st.subheader("Risk flags")
    st.write(result.risk_flags or ["No deterministic risk flags triggered."])
with right:
    st.subheader("Reviewer notes")
    st.write(result.reviewer_notes or ["No additional notes."])

st.subheader("Audit JSON")
st.json(result.to_dict())
st.download_button("Download audit JSON", json.dumps(result.to_dict(), indent=2), file_name="healthqa_audit.json", mime="application/json")

st.divider()
st.caption("Portfolio/research demonstration only. Not diagnosis, triage, treatment software, or a medical device.")
