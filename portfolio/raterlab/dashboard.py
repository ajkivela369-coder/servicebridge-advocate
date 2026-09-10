from __future__ import annotations

import io
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="RaterLab", page_icon="🎯", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2rem}
.hero{padding:1.25rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}
.kicker{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;opacity:.65}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.18);padding:.7rem;border-radius:14px}
</style>
""", unsafe_allow_html=True)

def accuracy(a, b):
    return float((a == b).mean()) if len(a) else 0.0

def kappa(a, b):
    if len(a) == 0:
        return 0.0
    po = accuracy(a, b)
    labels = sorted(set(a) | set(b))
    pa = a.value_counts(normalize=True)
    pb = b.value_counts(normalize=True)
    pe = sum(pa.get(x, 0) * pb.get(x, 0) for x in labels)
    return 1.0 if pe == 1 and po == 1 else round((po - pe) / (1 - pe), 3) if pe < 1 else 0.0

st.markdown('<div class="hero"><div class="kicker">AJ AI Evaluation Lab</div><h1>RaterLab</h1><p>Annotation QA, gold-set scoring, disagreement analysis, and inter-rater calibration.</p></div>', unsafe_allow_html=True)

sample = """item_id,gold,rater_a,rater_b
1,PASS,PASS,PASS
2,REVIEW,REVIEW,PASS
3,ESCALATE,ESCALATE,ESCALATE
4,PASS,PASS,PASS
5,REVIEW,PASS,REVIEW
6,ESCALATE,ESCALATE,REVIEW
7,PASS,PASS,PASS
8,REVIEW,REVIEW,REVIEW
9,ESCALATE,ESCALATE,ESCALATE
10,PASS,REVIEW,PASS"""

uploaded = st.file_uploader("Upload annotation CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    raw = st.text_area("Or edit the sample CSV", sample, height=220)
    df = pd.read_csv(io.StringIO(raw))

required = {"item_id","gold","rater_a","rater_b"}
missing = required - set(df.columns)
if missing:
    st.error("Missing columns: " + ", ".join(sorted(missing)))
    st.stop()

for c in ["gold","rater_a","rater_b"]:
    df[c] = df[c].astype(str).str.strip()

agree = accuracy(df["rater_a"], df["rater_b"])
kap = kappa(df["rater_a"], df["rater_b"])
acc_a = accuracy(df["gold"], df["rater_a"])
acc_b = accuracy(df["gold"], df["rater_b"])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Inter-rater agreement", f"{agree:.1%}")
c2.metric("Cohen's κ", f"{kap:.3f}")
c3.metric("Rater A vs gold", f"{acc_a:.1%}")
c4.metric("Rater B vs gold", f"{acc_b:.1%}")

tab1,tab2,tab3 = st.tabs(["Disagreement Queue","Label Distribution","Calibration Export"])
with tab1:
    disagreements = df[df["rater_a"] != df["rater_b"]].copy()
    st.dataframe(disagreements, use_container_width=True, hide_index=True)
    st.caption(f"{len(disagreements)} of {len(df)} items require calibration review.")
with tab2:
    dist = pd.DataFrame({
        "Gold": df["gold"].value_counts(),
        "Rater A": df["rater_a"].value_counts(),
        "Rater B": df["rater_b"].value_counts(),
    }).fillna(0).astype(int)
    st.bar_chart(dist)
    st.dataframe(dist, use_container_width=True)
with tab3:
    report = {
        "items": len(df),
        "agreement": round(agree, 4),
        "cohen_kappa": kap,
        "rater_a_gold_accuracy": round(acc_a, 4),
        "rater_b_gold_accuracy": round(acc_b, 4),
        "disagreement_item_ids": disagreements["item_id"].astype(str).tolist(),
    }
    st.json(report)
    st.download_button("Download calibration report", json.dumps(report, indent=2), "raterlab_report.json", "application/json")
    st.download_button("Download disagreement CSV", disagreements.to_csv(index=False), "raterlab_disagreements.csv", "text/csv")

st.caption("RaterLab demonstrates annotation-quality and calibration workflows. Agreement metrics measure consistency, not correctness by themselves.")
