from __future__ import annotations

import json
import re
from collections import Counter
import streamlit as st

st.set_page_config(page_title="CiteGuard", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2rem}
.hero{padding:1.25rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}
.kicker{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;opacity:.65}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.18);padding:.7rem;border-radius:14px}
</style>
""", unsafe_allow_html=True)

STOP = {"the","a","an","and","or","of","to","in","is","are","was","were","for","with","that","this","on","as","by","be","from","it"}
ABSOLUTES = {"proves","proven","always","never","guarantees","certainly","definitively","impossible"}

def tokens(text):
    return {w for w in re.findall(r"[a-zA-Z]{4,}", text.lower()) if w not in STOP}

def support_score(claim, source):
    ct, stt = tokens(claim), tokens(source)
    return round(len(ct & stt) / max(1, len(ct)), 2)

st.markdown('<div class="hero"><div class="kicker">AJ AI Evaluation Lab</div><h1>CiteGuard</h1><p>Scientific claim-to-source auditing for citation coverage, overclaim detection, and evidence-review routing.</p></div>', unsafe_allow_html=True)

claims_text = st.text_area("Claims — one per line", """Voltage-gated sodium channels contribute to the rapid depolarizing phase of many neuronal action potentials.
This mechanism proves that every neuron has identical channel kinetics.""", height=140)
sources_text = st.text_area("Source snippets — use SOURCE_ID | text", """SRC-01 | Electrophysiology studies describe rapid depolarization mediated by voltage-gated sodium channel opening, followed by potassium-dependent repolarization.
SRC-02 | Ion-channel kinetics vary across neuronal classes, membrane compartments, and experimental conditions.""", height=160)

claims = [x.strip() for x in claims_text.splitlines() if x.strip()]
sources = []
for line in sources_text.splitlines():
    if "|" in line:
        sid, text = line.split("|", 1)
        sources.append((sid.strip(), text.strip()))

threshold = st.sidebar.slider("Support threshold", .05, .80, .25, .05)
records = []
for i, claim in enumerate(claims, 1):
    ranked = sorted([(support_score(claim, txt), sid, txt) for sid, txt in sources], reverse=True)
    best_score, best_id, best_text = ranked[0] if ranked else (0, "NONE", "")
    overclaim = sorted(tokens(claim) & ABSOLUTES)
    status = "SUPPORTED" if best_score >= threshold else "REVIEW"
    if overclaim:
        status = "REVIEW"
    if best_score < max(.05, threshold / 2):
        status = "UNSUPPORTED"
    records.append({
        "claim_id": f"C{i:02}",
        "claim": claim,
        "status": status,
        "best_source": best_id,
        "lexical_support": best_score,
        "overclaim_terms": overclaim,
        "source_excerpt": best_text,
    })

counts = Counter(r["status"] for r in records)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Claims", len(records))
c2.metric("Supported", counts["SUPPORTED"])
c3.metric("Review", counts["REVIEW"])
c4.metric("Unsupported", counts["UNSUPPORTED"])

st.subheader("Claim audit")
for r in records:
    with st.expander(f"{r['claim_id']} · {r['status']} · best source {r['best_source']} · overlap {r['lexical_support']:.0%}", expanded=r["status"] != "SUPPORTED"):
        st.write(r["claim"])
        if r["overclaim_terms"]:
            st.warning("Absolute / overclaim language: " + ", ".join(r["overclaim_terms"]))
        st.write("**Best matching source snippet**")
        st.write(r["source_excerpt"] or "No source provided.")

st.subheader("Audit table")
st.dataframe(records, use_container_width=True, hide_index=True)
payload = {"support_threshold": threshold, "claims": records, "method_note": "Lexical overlap baseline; human source verification required."}
st.download_button("Download citation audit JSON", json.dumps(payload, indent=2), "citeguard_audit.json", "application/json")
st.caption("CiteGuard is an auditable baseline, not an automated fact checker. A high overlap score does not prove that a source actually supports a claim.")
