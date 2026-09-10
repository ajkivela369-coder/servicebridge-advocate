from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from neuroeval import evaluate

st.set_page_config(page_title="NeuroEval", page_icon="🧠", layout="wide")
st.title("NeuroEval — Biology & Neuroscience AI Evaluator")
st.caption("Transparent scoring for model outputs: concept coverage, mechanism, uncertainty, evidence language, and clarity.")

sample = "Action potentials propagate because voltage-gated sodium channels open, followed by potassium-mediated repolarization. Evidence supports this mechanism, although channel kinetics can vary across cell types."
answer = st.text_area("AI-generated answer", value=sample, height=180)
concept_text = st.text_input("Required concepts (comma-separated)", "sodium channels, potassium, repolarization")
concepts = [x.strip() for x in concept_text.split(",") if x.strip()]

result = evaluate(answer, concepts)
cols = st.columns(6)
for col, label, value in zip(cols, ["Total", "Factuality", "Mechanism", "Uncertainty", "Evidence", "Clarity"], [result.total, result.factuality, result.mechanism, result.uncertainty, result.evidence_language, result.clarity]):
    col.metric(label, f"{value}{'%' if label == 'Total' else '/5'}")

left, right = st.columns(2)
with left:
    st.subheader("Strengths")
    st.write(result.strengths or ["No rubric strength triggered."])
with right:
    st.subheader("Flags")
    st.write(result.flags or ["No deterministic flags triggered."])

st.subheader("Reviewer JSON")
st.json(result.to_dict())
st.download_button("Download evaluation JSON", json.dumps(result.to_dict(), indent=2), file_name="neuroeval_result.json", mime="application/json")

st.divider()
st.caption("Portfolio/research demonstration only. Deterministic baseline; not a medical device or source of patient-specific advice.")
