from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from coverage import assess_issue_coverage
from page_copilot import render_page_copilot
from quote_integrity import verify_quote_contextual
from readiness import assess_provenance_readiness
from ui_shell import render_app_nav, workspace_status

st.set_page_config(page_title="Case Review · Evidence Auditor Pro", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")
render_app_nav("review")

st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"]{display:none}
    .block-container{max-width:1320px;padding-top:1rem;padding-bottom:5rem}
    .hero{border:1px solid rgba(100,116,139,.18);border-radius:20px;padding:1.15rem 1.25rem;background:rgba(100,116,139,.025);margin-bottom:1rem}
    .hero h1{font-size:1.75rem;letter-spacing:-.025em;margin:0 0 .35rem}.hero p{opacity:.68;margin:0;max-width:900px;line-height:1.5}
    .review-card{border:1px solid rgba(100,116,139,.18);border-radius:15px;padding:.85rem;background:rgba(100,116,139,.025)}
    .passage{border-left:3px solid rgba(37,99,235,.55);padding:.2rem 0 .2rem .8rem;line-height:1.5}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="hero"><h1>Case Review</h1><p>One place for evidence quality control: provenance, issue coverage, source-backed passages, quote verification, contradictions, record gaps, and source inventory. Elias remains the conversational front door.</p></div>""",
    unsafe_allow_html=True,
)

sources, result = workspace_status()
if not sources or not result:
    st.warning("No case record is loaded in this session. Add the documents once in Elias, then come back here for structured review.")
    st.page_link("dashboard.py", label="Open Elias and add case files →", icon="💬", use_container_width=True)
    st.stop()

provenance = assess_provenance_readiness(sources)
coverage = assess_issue_coverage(result.get("items", []))
summary = result.get("summary", {})

m1, m2, m3, m4, m5 = st.columns(5, gap="small")
m1.metric("Provenance", f"{provenance['score']}%")
m2.metric("Issues", coverage.get("issue_count", 0))
m3.metric("Favorable", summary.get("favorable", 0))
m4.metric("Tensions", len(result.get("potential_contradictions", [])))
m5.metric("Gap signals", len(result.get("missing_record_flags", [])))

tabs = st.tabs(["Overview", "Evidence", "Quotes", "Gaps & tensions", "Sources"])

with tabs[0]:
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("### Provenance readiness")
        st.progress(provenance["score"] / 100 if provenance["score"] else 0)
        st.write(f"**{provenance['grade']}**")
        for flag in provenance.get("flags", []):
            st.caption(flag)
        st.markdown("### Issue coverage")
        c1, c2, c3 = st.columns(3)
        c1.metric("Strong", coverage.get("strong", 0))
        c2.metric("Developing", coverage.get("developing", 0))
        c3.metric("Thin", coverage.get("thin", 0))
    with right:
        st.markdown("### Issue map")
        if result.get("issue_summary"):
            st.bar_chart(result["issue_summary"], horizontal=True)
        else:
            st.info("No issue groups were detected in the loaded record.")
        st.caption("Scores measure review depth and traceability, not legal or medical merit.")

with tabs[1]:
    st.markdown("### Source-backed evidence")
    f1, f2 = st.columns([1, 1])
    with f1:
        stance = st.multiselect(
            "Stance",
            ["favorable", "unfavorable", "mixed", "neutral"],
            default=["favorable", "unfavorable", "mixed", "neutral"],
        )
    with f2:
        min_conf = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05)
    visible = [i for i in result.get("items", []) if i.get("stance") in stance and float(i.get("confidence", 0)) >= min_conf]
    for item in visible:
        loc = item.get("source_name", "Unknown source") + (f" · p. {item['page']}" if item.get("page") else "")
        title = f"{item.get('stance','neutral').upper()} · {float(item.get('confidence',0)):.0%} · {loc}"
        with st.expander(title, expanded=item.get("stance") in {"favorable", "unfavorable", "mixed"}):
            st.markdown(f'<div class="passage">{item.get("text", "")}</div>', unsafe_allow_html=True)
            issues = ", ".join(x.replace("_", " ").title() for x in item.get("issues", [])) or "General evidence"
            st.caption(f"Issues: {issues} · Source type: {item.get('source_type','unspecified').replace('_',' ').title()}")

with tabs[2]:
    st.markdown("### Quote verifier")
    quote = st.text_area("Paste the exact wording you want to use", height=120, placeholder="Paste a proposed verbatim quotation here…")
    if quote.strip():
        check = verify_quote_contextual(quote, sources)
        if check["status"] == "verified":
            st.success(check["note"])
        elif check["status"] == "partial":
            st.warning(check["note"])
        else:
            st.error(check["note"])
        for match in check.get("matches", [])[:5]:
            loc = match.get("source_name", "Unknown source") + (f", p. {match['page']}" if match.get("page") else "")
            st.write(f"**{loc}** · {match.get('match_type','').replace('_',' ')} · {match.get('score',0):.0%}")
            context = match.get("context", {})
            if context.get("before"):
                st.caption("Before: " + context["before"])
            if context.get("match"):
                st.markdown("**Match/context:** " + context["match"])
            if context.get("after"):
                st.caption("After: " + context["after"])
    st.caption("A text match verifies wording only. It does not establish medical truth, legal weight, or authenticity by itself.")

with tabs[3]:
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("### Priority coverage gaps")
        gaps = coverage.get("priority_gaps", [])
        if not gaps:
            st.success("No priority issue-coverage gap was detected by this screening pass.")
        for gap in gaps[:10]:
            label = str(gap.get("issue", "unknown")).replace("_", " ").title()
            with st.expander(f"{label} · {gap.get('coverage_score',0)}/100 · {gap.get('coverage_band','thin').title()}"):
                for flag in gap.get("flags", []):
                    st.write("• " + flag)
    with right:
        st.markdown("### Record-gap signals")
        flags = result.get("missing_record_flags", [])
        if not flags:
            st.success("No deterministic missing-record signal was detected.")
        for flag in flags[:10]:
            loc = flag.get("source_name", "Unknown source") + (f", p. {flag['page']}" if flag.get("page") else "")
            st.warning(f"{flag.get('text','')} — {loc}")

    st.markdown("### Supporting vs. adverse tensions")
    tensions = result.get("potential_contradictions", [])
    if not tensions:
        st.info("No same-issue cross-stance tension was detected by this screening pass.")
    for idx, tension in enumerate(tensions[:12], 1):
        issues = ", ".join(x.replace("_", " ").title() for x in tension.get("issues", [])) or "Shared issue"
        st.markdown(f"**Tension {idx} · {issues}**")
        c1, c2 = st.columns(2, gap="large")
        fav = tension.get("favorable", {})
        unf = tension.get("unfavorable", {})
        with c1:
            st.success("Supporting")
            st.write(fav.get("text", ""))
            st.caption(fav.get("source_name", "Unknown source") + (f" · p. {fav['page']}" if fav.get("page") else ""))
        with c2:
            st.error("Adverse / opposing")
            st.write(unf.get("text", ""))
            st.caption(unf.get("source_name", "Unknown source") + (f" · p. {unf['page']}" if unf.get("page") else ""))
        st.divider()

with tabs[4]:
    st.markdown("### Source inventory")
    rows = []
    for source in sources:
        text = str(source.get("text") or "")
        rows.append(
            {
                "Source": source.get("source_name", "Unknown source"),
                "Page": source.get("page"),
                "Text extracted": "Yes" if text.strip() else "No",
                "Characters": len(text),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("Image-only or blank extracted pages should be manually reviewed or routed to OCR; absence of extracted text is not proof that the page contains no evidence.")

render_page_copilot()
