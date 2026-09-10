from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quote_integrity import verify_quote_contextual

st.set_page_config(page_title="Quote Integrity · Evidence Auditor Pro", page_icon="🔎", layout="wide")

st.markdown(
    """
    <style>
    .block-container{max-width:1450px;padding-top:1.35rem;padding-bottom:3rem}
    .qi-hero{padding:1.35rem 1.5rem;border-radius:22px;background:linear-gradient(135deg,#111c35,#27456f);color:white;margin-bottom:1rem}
    .qi-kicker{font-size:.70rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.70}
    .qi-title{font-size:2rem;font-weight:800;margin:.25rem 0 .35rem}
    .qi-copy{opacity:.84;line-height:1.5;max-width:980px}
    .qi-card{border:1px solid rgba(120,130,150,.20);border-radius:16px;padding:1rem;background:rgba(120,130,150,.035)}
    .qi-verified{border-left:5px solid #20a66a}.qi-partial{border-left:5px solid #d89a34}.qi-missing{border-left:5px solid #d85b5b}
    .qi-label{font-size:.70rem;text-transform:uppercase;letter-spacing:.10em;font-weight:800;opacity:.60}
    .qi-context{border:1px solid rgba(120,130,150,.17);border-radius:12px;padding:.8rem .9rem;margin:.45rem 0;background:rgba(120,130,150,.025)}
    .qi-match{font-weight:700}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="qi-hero"><div class="qi-kicker">Evidence integrity workspace</div>
    <div class="qi-title">Quote Integrity</div>
    <div class="qi-copy">Check whether proposed quotation language actually appears in a source PDF, inspect the surrounding sentence context, and distinguish exact verification from merely similar wording before the text reaches a packet.</div></div>""",
    unsafe_allow_html=True,
)


def extract_sources(uploaded_files):
    sources=[]
    for uploaded in uploaded_files:
        try:
            uploaded.seek(0)
            reader=PdfReader(uploaded)
            for page_no,page in enumerate(reader.pages,1):
                text=(page.extract_text() or "").strip()
                if text:
                    sources.append({"source_name":uploaded.name,"page":page_no,"text":text})
        except Exception as exc:
            st.warning(f"Could not extract {uploaded.name}: {exc}")
    return sources

left,right=st.columns([1.1,1],gap="large")
with left:
    uploaded=st.file_uploader("Source PDFs",type=["pdf"],accept_multiple_files=True,help="Use fictional or de-identified material in public deployments.")
    quote=st.text_area("Proposed quotation",height=150,placeholder="Paste the wording you intend to quote...")
with right:
    st.markdown("#### Verification levels")
    st.markdown(
        """<div class="qi-card"><b>Verified</b> — normalized exact text appears in the source.<br><br>
        <b>Partial</b> — similar language exists, but the wording is not exact and should not be presented as verbatim.<br><br>
        <b>Not found</b> — no sufficiently similar source language was located.</div>""",
        unsafe_allow_html=True,
    )
    st.caption("Whitespace and common smart-quote differences are normalized. Similarity never upgrades a non-exact quote into a verified quote.")

sources=extract_sources(uploaded or [])

if uploaded:
    st.caption(f"Indexed {len(sources)} text-bearing PDF pages from {len(uploaded)} uploaded file(s).")

if quote.strip() and sources:
    result=verify_quote_contextual(quote,sources)
    status=result["status"]
    css={"verified":"qi-verified","partial":"qi-partial","not_found":"qi-missing"}.get(status,"")
    title={"verified":"VERIFIED QUOTE","partial":"SIMILAR, NOT EXACT","not_found":"NOT VERIFIED"}.get(status,status.upper())
    score=result.get("confidence",0.0)
    st.markdown(f'<div class="qi-card {css}"><div class="qi-label">{title}</div><h3>{score:.0%} match confidence</h3>{result["note"]}</div>',unsafe_allow_html=True)

    for match in result.get("matches",[]):
        if not match:
            continue
        loc=match.get("source_name","Unknown source")+(f", p. {match['page']}" if match.get("page") else "")
        st.markdown(f"#### {loc}")
        context=match.get("context",{})
        c1,c2,c3=st.columns([1,1.4,1],gap="small")
        with c1:
            st.markdown('<div class="qi-label">Before</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="qi-context">{context.get("before") or "—"}</div>',unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="qi-label">Matched source language</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="qi-context qi-match">{context.get("match") or "—"}</div>',unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="qi-label">After</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="qi-context">{context.get("after") or "—"}</div>',unsafe_allow_html=True)
        st.caption(f"Match type: {match.get('match_type','unknown')} · score {match.get('score',0):.0%}")
elif quote.strip() and not sources:
    st.info("Upload at least one text-bearing source PDF to verify the quotation.")
else:
    st.info("Add source PDFs and a proposed quotation to begin.")

st.divider()
st.caption("Evidence Auditor Pro does not determine whether a statement is medically true, legally sufficient, or properly interpreted. Quote Integrity verifies source wording and context only.")
