from __future__ import annotations

import json
import streamlit as st

st.set_page_config(page_title="Benchmark Forge", page_icon="🧪", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2rem}
.hero{padding:1.25rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}
.kicker{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;opacity:.65}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.18);padding:.7rem;border-radius:14px}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="kicker">AJ AI Evaluation Lab</div><h1>Benchmark Forge</h1><p>Create structured evaluation items with prompts, gold labels, expected concepts, misconceptions, difficulty, and reviewer rationale.</p></div>', unsafe_allow_html=True)

if "bench_items" not in st.session_state:
    st.session_state.bench_items = [
        {
            "id":"NEURO-001",
            "domain":"neuroscience",
            "difficulty":"medium",
            "prompt":"Explain the ionic basis of neuronal action-potential repolarization.",
            "expected_concepts":["voltage-gated potassium channels","potassium efflux"],
            "prohibited_misconceptions":["repolarization is caused only by sodium influx"],
            "gold_label":"PASS",
            "reviewer_rationale":"A complete answer should identify potassium conductance as a major repolarizing mechanism while allowing physiological nuance."
        }
    ]

with st.sidebar:
    st.header("Benchmark health")
    items = st.session_state.bench_items
    st.metric("Items", len(items))
    st.metric("Domains", len({x["domain"] for x in items}))
    st.metric("With rationale", sum(bool(x["reviewer_rationale"]) for x in items))
    if st.button("Reset demo set"):
        st.session_state.bench_items = []
        st.rerun()

st.subheader("Author a benchmark item")
with st.form("builder", clear_on_submit=True):
    c1,c2,c3 = st.columns(3)
    item_id = c1.text_input("Item ID", f"ITEM-{len(st.session_state.bench_items)+1:03}")
    domain = c2.text_input("Domain", "neuroscience")
    difficulty = c3.selectbox("Difficulty", ["easy","medium","hard","expert"], index=1)
    prompt = st.text_area("Prompt", height=100)
    expected = st.text_input("Expected concepts — comma separated")
    prohibited = st.text_input("Prohibited misconceptions — comma separated")
    label = st.selectbox("Gold / expected disposition", ["PASS","REVIEW","FAIL","ESCALATE"])
    rationale = st.text_area("Gold rationale / reviewer guidance", height=100)
    add = st.form_submit_button("Add benchmark item", type="primary")

if add:
    problems = []
    if not item_id.strip(): problems.append("Item ID is required.")
    if not prompt.strip(): problems.append("Prompt is required.")
    if any(x["id"] == item_id.strip() for x in st.session_state.bench_items): problems.append("Item ID must be unique.")
    if problems:
        for p in problems: st.error(p)
    else:
        st.session_state.bench_items.append({
            "id": item_id.strip(),
            "domain": domain.strip() or "general",
            "difficulty": difficulty,
            "prompt": prompt.strip(),
            "expected_concepts": [x.strip() for x in expected.split(",") if x.strip()],
            "prohibited_misconceptions": [x.strip() for x in prohibited.split(",") if x.strip()],
            "gold_label": label,
            "reviewer_rationale": rationale.strip(),
        })
        st.success(f"Added {item_id.strip()}")

items = st.session_state.bench_items
st.subheader("Benchmark dataset")
if items:
    st.dataframe(items, use_container_width=True, hide_index=True)
    domains = {}
    for x in items:
        domains[x["domain"]] = domains.get(x["domain"], 0) + 1
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Items", len(items))
    c2.metric("Domains", len(domains))
    c3.metric("Hard / expert", sum(x["difficulty"] in {"hard","expert"} for x in items))
    c4.metric("Missing rationale", sum(not x["reviewer_rationale"] for x in items))

    st.subheader("Domain coverage")
    st.bar_chart(domains)

    jsonl = "\n".join(json.dumps(x, ensure_ascii=False) for x in items)
    st.download_button("Download benchmark JSONL", jsonl, "benchmark_forge.jsonl", "application/json")
    st.download_button("Download benchmark JSON", json.dumps(items, indent=2), "benchmark_forge.json", "application/json")
else:
    st.info("No benchmark items yet. Add one above.")

st.caption("Benchmark Forge is a portfolio tool for transparent evaluation-set authoring. Gold labels and rationales still require qualified human review.")
