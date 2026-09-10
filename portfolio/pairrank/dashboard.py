from __future__ import annotations

import json
from dataclasses import dataclass, asdict
import streamlit as st

st.set_page_config(page_title="PairRank", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2rem}
.hero{padding:1.25rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}
.kicker{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;opacity:.65}
.small{opacity:.72;font-size:.92rem}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.18);padding:.7rem;border-radius:14px}
</style>
""", unsafe_allow_html=True)

CRITERIA = ["Accuracy", "Relevance", "Reasoning", "Clarity", "Safety"]

@dataclass
class Review:
    response: str
    scores: dict
    weighted_score: float
    notes: str

    def to_dict(self):
        return asdict(self)

def weighted(scores: dict, weights: dict) -> float:
    denom = sum(weights.values()) or 1
    return round(sum(scores[k] * weights[k] for k in CRITERIA) / denom, 2)

st.markdown('<div class="hero"><div class="kicker">AJ AI Evaluation Lab</div><h1>PairRank</h1><p>Pairwise LLM response evaluation with weighted rubrics, preference labels, failure tags, and reviewer rationale.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Rubric weights")
    weights = {k: st.slider(k, 0, 5, 3 if k != "Accuracy" else 5) for k in CRITERIA}
    st.divider()
    st.caption("Designed to mirror human-evaluator workflows. Scores are reviewer judgments, not ground truth.")

prompt = st.text_area("Prompt / task", "Explain why action potentials are all-or-none events.", height=90)
left, right = st.columns(2)
with left:
    st.subheader("Response A")
    a_text = st.text_area("A", "An action potential occurs once membrane depolarization reaches threshold. Voltage-gated sodium channel opening creates positive feedback, so a full spike is generated rather than a proportionally smaller one.", height=180, label_visibility="collapsed")
with right:
    st.subheader("Response B")
    b_text = st.text_area("B", "Action potentials are all-or-none because neurons always fire at maximum strength whenever they receive any signal.", height=180, label_visibility="collapsed")

st.subheader("Reviewer scoring")
a_col, b_col = st.columns(2)
a_scores, b_scores = {}, {}
with a_col:
    st.markdown("**Score Response A**")
    for c in CRITERIA:
        a_scores[c] = st.slider(f"A · {c}", 1, 5, 4, key=f"a_{c}")
    a_notes = st.text_area("A reviewer notes", "Mechanistically specific and appropriately scoped.")
with b_col:
    st.markdown("**Score Response B**")
    for c in CRITERIA:
        b_scores[c] = st.slider(f"B · {c}", 1, 5, 3, key=f"b_{c}")
    b_notes = st.text_area("B reviewer notes", "Overgeneralizes threshold behavior and uses absolute language.")

a_total, b_total = weighted(a_scores, weights), weighted(b_scores, weights)
if abs(a_total - b_total) < .15:
    preference = "TIE / BOTH NEED REVIEW"
elif a_total > b_total:
    preference = "A PREFERRED"
else:
    preference = "B PREFERRED"

m1, m2, m3 = st.columns(3)
m1.metric("Response A", f"{a_total:.2f}/5")
m2.metric("Response B", f"{b_total:.2f}/5")
m3.metric("Preference", preference)

tags = st.multiselect("Failure / review tags", [
    "factual error", "unsupported claim", "instruction-following", "missing nuance",
    "unsafe content", "overconfidence", "verbosity", "poor reasoning", "ambiguous prompt"
])
rationale = st.text_area("Pairwise justification", f"{preference}: Response A provides the stronger mechanistic explanation and is better calibrated to the task.")

record = {
    "prompt": prompt,
    "weights": weights,
    "response_a": Review(a_text, a_scores, a_total, a_notes).to_dict(),
    "response_b": Review(b_text, b_scores, b_total, b_notes).to_dict(),
    "preference": preference,
    "failure_tags": tags,
    "rationale": rationale,
}

with st.expander("Machine-readable evaluation record"):
    st.json(record)

st.download_button("Download pairwise review JSON", json.dumps(record, indent=2), "pairrank_review.json", "application/json")
st.caption("Portfolio/research demonstration. Human-scored evaluation workflow; not a claim that reviewer preference is objective ground truth.")
