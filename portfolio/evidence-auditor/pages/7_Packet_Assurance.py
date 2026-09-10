from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditor import audit_sources
from packet_assurance import assess_packet_assurance
from page_copilot import render_page_copilot

st.set_page_config(page_title="Packet Assurance · Evidence Auditor Pro", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    .block-container{max-width:1450px;padding-top:1.1rem;padding-bottom:3rem}
    .assure-hero{padding:1.4rem 1.55rem;border-radius:22px;color:white;background:
      radial-gradient(circle at 82% 8%,rgba(56,189,248,.24),transparent 30%),
      radial-gradient(circle at 12% 25%,rgba(52,211,153,.16),transparent 28%),
      linear-gradient(135deg,#0f172a,#1e293b 58%,#243b53);margin-bottom:1rem;box-shadow:0 18px 50px rgba(0,0,0,.18)}
    .eyebrow{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;opacity:.68}
    .headline{font-size:2rem;font-weight:820;margin:.2rem 0 .35rem}
    .sub{max-width:930px;opacity:.82;line-height:1.55}
    .score-card{border:1px solid rgba(100,116,139,.22);border-radius:18px;padding:1rem 1.1rem;background:rgba(100,116,139,.035)}
    .score-big{font-size:2.2rem;font-weight:850;line-height:1}
    .score-label{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;opacity:.62;font-weight:800;margin-top:.35rem}
    .band{display:inline-block;margin-top:.5rem;padding:.22rem .52rem;border-radius:999px;background:rgba(37,99,235,.09);font-size:.76rem;font-weight:800}
    .blocker{border-left:4px solid #d97706;border-radius:10px;padding:.65rem .8rem;background:rgba(217,119,6,.06);margin:.4rem 0}
    .good{border-left-color:#059669;background:rgba(5,150,105,.06)}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="assure-hero"><div class="eyebrow">Reviewer trust layer · Evidence Auditor Pro</div>
    <div class="headline">Packet Assurance</div>
    <div class="sub">One screen for provenance quality, source reconciliation, evidence-depth gaps, and verbatim-quote integrity. The score measures reviewer readiness—not claim merit, legal sufficiency, medical causation, or eligibility.</div></div>""",
    unsafe_allow_html=True,
)


def read_pdfs(files):
    sources = []
    for uploaded in files or []:
        try:
            uploaded.seek(0)
            reader = PdfReader(uploaded)
            for page_number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").strip()
                sources.append({"source_name": uploaded.name, "page": page_number, "text": text})
        except Exception as exc:
            st.warning(f"Could not read {uploaded.name}: {exc}")
    return sources


left, right = st.columns([1.55, 1], gap="large")
with left:
    files = st.file_uploader(
        "Source PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="For a public deployment, use fictional or thoroughly de-identified records only.",
    )
with right:
    proposed = st.text_area(
        "Proposed verbatim quotations",
        placeholder="One quotation per line. Leave blank if the packet contains no verbatim quotes.",
        height=130,
    )

sources = read_pdfs(files)
if not sources:
    demo = [
        {"source_name": "synthetic_exam.pdf", "page": 2, "text": "The clinician documented objective functional limitation during duty."},
        {"source_name": "synthetic_followup.pdf", "page": 4, "text": "A follow-up note documented continued functional limitation and restricted activity."},
        {"source_name": "synthetic_notice.pdf", "page": 1, "text": "Several service records were unavailable for review."},
    ]
    sources = demo
    st.info("Using a fictional demonstration record until PDFs are loaded.")

result = audit_sources(sources)
quotes = [line.strip() for line in proposed.splitlines() if line.strip()]
assurance = assess_packet_assurance(result.get("items", []), sources, quotes)

cards = st.columns(4, gap="small")
for col, label, value in [
    (cards[0], "Assurance", assurance["score"]),
    (cards[1], "Provenance", assurance["provenance_score"]),
    (cards[2], "Coverage", assurance["coverage_score"]),
    (cards[3], "Quote integrity", assurance["quote_score"]),
]:
    with col:
        st.markdown(f'<div class="score-card"><div class="score-big">{value}</div><div class="score-label">{label}</div></div>', unsafe_allow_html=True)

st.markdown(f'**Readiness band:** `{assurance["band"].replace("_", " ").title()}`')

if assurance["blockers"]:
    st.markdown("### Review blockers")
    for blocker in assurance["blockers"]:
        st.markdown(f'<div class="blocker">{blocker}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="blocker good"><b>No assurance blockers detected by this screening pass.</b> Human source review is still required.</div>', unsafe_allow_html=True)

p1, p2, p3 = st.columns(3, gap="large")
with p1:
    st.markdown("### Provenance")
    provenance = assurance["provenance"]
    st.metric("Named source units", f'{provenance["named_source_pct"]}%')
    st.metric("Page-locatable units", f'{provenance["page_locator_pct"]}%')
    st.metric("Usable text units", f'{provenance["usable_text_pct"]}%')
    for flag in provenance.get("flags", []):
        st.caption("• " + flag)
with p2:
    st.markdown("### Coverage")
    coverage = assurance["coverage"]
    st.metric("Strong issues", coverage.get("strong", 0))
    st.metric("Developing issues", coverage.get("developing", 0))
    st.metric("Thin issues", coverage.get("thin", 0))
    for issue in coverage.get("priority_gaps", [])[:4]:
        st.caption(f'• {issue["issue"].replace("_", " ").title()}: {issue["coverage_score"]}/100')
with p3:
    st.markdown("### Quote integrity")
    q = assurance["quotes"]
    st.metric("Verified", q["counts"]["verified"])
    st.metric("Similar / not verbatim", q["counts"]["partial"])
    st.metric("Not found", q["counts"]["not_found"])
    if not q["quote_count"]:
        st.caption("No proposed verbatim quotations entered.")

inventory = assurance.get("source_inventory", {})
st.markdown("### Source reconciliation")
ri1, ri2, ri3 = st.columns(3, gap="small")
ri1.metric("Documents", inventory.get("document_count", 0))
ri2.metric("Ready", max(0, inventory.get("document_count", 0) - inventory.get("documents_needing_review", 0)))
ri3.metric("Need review", inventory.get("documents_needing_review", 0))

inventory_rows = []
for doc in inventory.get("documents", []):
    inventory_rows.append({
        "Status": doc.get("status", "review").title(),
        "Source ID": doc.get("source_id", "—"),
        "Document": doc.get("source_name", "Unknown source"),
        "Observed pages": doc.get("page_range", "—"),
        "Text pages": doc.get("text_pages", 0),
        "Blank/unextractable": doc.get("blank_pages", "—"),
        "Missing in range": doc.get("missing_pages", "—"),
        "Unpaged units": doc.get("unpaged_units", 0),
    })
if inventory_rows:
    st.dataframe(inventory_rows, use_container_width=True, hide_index=True)
    for doc in inventory.get("documents", []):
        if doc.get("flags"):
            with st.expander(f'{doc.get("source_name", "Unknown source")} · {doc.get("source_id", "—")} · review cues'):
                for flag in doc.get("flags", []):
                    st.warning(flag)
    st.caption(inventory.get("note", ""))
else:
    st.caption("No source inventory is available for the current packet.")

if assurance["quotes"]["results"]:
    st.markdown("### Verification register")
    for item in assurance["quotes"]["results"]:
        with st.expander(f'{item["quote_id"]} · {item["status"].replace("_", " ").title()} · {item["confidence"]:.0%}'):
            st.write(item["quote"])
            for match in item.get("matches", [])[:3]:
                source = match.get("source_name") or "Unknown source"
                page = match.get("page")
                source_id = match.get("source_id") or ""
                locator = f"{source}, p. {page}" if page else source
                if source_id:
                    locator += f" · {source_id}"
                st.caption(locator)
                context = match.get("context") or {}
                before = context.get("before") or ""
                after = context.get("after") or ""
                if before or after:
                    st.write(f"…{before} **[{match.get('matched_text', item['quote'])}]** {after}…")

st.divider()
st.caption(assurance["note"] + " Public examples are fictional/de-identified; do not use a public deployment for sensitive records unless its data-handling controls are appropriate.")

render_page_copilot(sources=sources, result=result)
