from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from copilot_engine import answer_question
from auditor import audit_sources
from packet_assurance import assess_packet_assurance
from packet_builder import build_packet

st.set_page_config(page_title="Elias · Start Here", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .block-container{padding-top:1.1rem;max-width:1450px}
    .elias-hero{padding:1.45rem 1.55rem;border-radius:24px;color:white;background:
      radial-gradient(circle at 80% 5%,rgba(102,126,234,.34),transparent 30%),
      radial-gradient(circle at 15% 25%,rgba(0,210,180,.18),transparent 32%),
      linear-gradient(135deg,#101827,#1d2c49 58%,#233b63);box-shadow:0 20px 55px rgba(0,0,0,.20);margin-bottom:1.15rem}
    .elias-name{font-size:2.15rem;font-weight:820;letter-spacing:-.02em;margin:.15rem 0 .3rem}
    .elias-role{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;opacity:.68}
    .elias-copy{max-width:900px;line-height:1.55;opacity:.86}
    .portrait{width:88px;height:88px;border-radius:50%;display:grid;place-items:center;font-size:2rem;font-weight:900;
      background:linear-gradient(145deg,#dbeafe,#93c5fd 52%,#5eead4);color:#14213d;border:3px solid rgba(255,255,255,.45);box-shadow:0 10px 28px rgba(0,0,0,.22)}
    .status{display:inline-flex;align-items:center;gap:.35rem;padding:.28rem .55rem;border-radius:999px;background:rgba(255,255,255,.09);font-size:.76rem;font-weight:700;margin-top:.65rem}
    .dot{width:7px;height:7px;border-radius:50%;background:#5eead4;box-shadow:0 0 10px #5eead4}
    .voice-card{border:1px solid rgba(90,110,150,.22);border-radius:18px;padding:1rem 1.05rem;background:linear-gradient(135deg,rgba(29,78,216,.06),rgba(15,118,110,.04))}
    .micro{font-size:.79rem;opacity:.68;line-height:1.45}
    .source-pill{display:inline-block;border:1px solid rgba(90,110,150,.2);border-radius:999px;padding:.22rem .5rem;margin:.12rem;font-size:.72rem}
    .intake{border:1px solid rgba(37,99,235,.20);border-radius:20px;padding:1.05rem 1.1rem;background:linear-gradient(135deg,rgba(37,99,235,.055),rgba(16,185,129,.035));margin:.4rem 0 1rem}
    .step-card{border:1px solid rgba(100,116,139,.20);border-radius:15px;padding:.85rem;background:rgba(100,116,139,.03);min-height:112px}
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_pdf_sources(uploaded_files):
    extracted = []
    for uploaded in uploaded_files or []:
        try:
            uploaded.seek(0)
            reader = PdfReader(uploaded)
            for page_number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").strip()
                if text:
                    extracted.append({"source_name": uploaded.name, "page": page_number, "text": text})
        except Exception as exc:
            st.warning(f"Could not read {uploaded.name}: {exc}")
    return extracted


hero_l, hero_r = st.columns([5, 1], vertical_alignment="center")
with hero_l:
    st.markdown(
        """
        <div class="elias-hero">
          <div class="elias-role">Evidence Auditor Pro · Start here</div>
          <div class="elias-name">Elias</div>
          <div class="elias-copy">Upload the record once. Elias organizes the evidence, keeps page-level provenance attached, answers source-grounded questions, surfaces gaps and contradictions, and can assemble a reviewer-ready evidence packet draft for human verification.</div>
          <div class="status"><span class="dot"></span> Citation-first · source-locatable · human review required</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_r:
    st.markdown('<div class="portrait">E</div>', unsafe_allow_html=True)

sources = st.session_state.get("ea_sources")
result = st.session_state.get("ea_result")

st.markdown('<div class="intake"><b>Case Intake</b><br><span class="micro">Put the source PDFs here first. The same session record is then available to the other Evidence Auditor workspaces and the floating Copilot.</span></div>', unsafe_allow_html=True)
quick_files = st.file_uploader(
    "Upload source PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    key="elias_pdf_loader_v2",
    help="For a public deployment, use fictional or thoroughly de-identified documents only. Sensitive records belong only in an appropriately controlled deployment.",
)
if quick_files:
    quick_sources = extract_pdf_sources(quick_files)
    if quick_sources:
        sources = quick_sources
        result = audit_sources(sources)
        st.session_state["ea_sources"] = sources
        st.session_state["ea_result"] = result
        st.success(f"Loaded {len(quick_files)} PDF(s) across {len(sources)} text-bearing pages. Elias and Copilot now share this record for the session.")

if sources and result:
    s1, s2, s3, s4 = st.columns(4, gap="small")
    s1.metric("Passages", len(result.get("items", [])))
    s2.metric("Source/page units", result.get("source_count", 0))
    s3.metric("Tensions", len(result.get("potential_contradictions", [])))
    s4.metric("Gap signals", len(result.get("missing_record_flags", [])))

    with st.expander("One-click packet draft", expanded=False):
        st.caption("This creates a source-backed reviewer draft, not a final legal or medical determination. Verify every quotation, source page, and conclusion before filing.")
        packet_title = st.text_input("Packet title", value="VA Evidence Review Packet — Draft for Human Review")
        packet_summary = st.text_area(
            "Executive summary",
            value="This packet organizes the loaded source record, favorable and adverse evidence, potential contradictions, record gaps, and source/page locators for human review.",
            height=90,
        )
        assurance = assess_packet_assurance(result.get("items", []), sources, [])
        st.caption(f"Packet assurance screen: {assurance['score']}/100 · {assurance['band'].replace('_',' ').title()}")
        try:
            packet_bytes = build_packet(
                result,
                packet_style="visual_claim",
                case_title=packet_title,
                executive_summary=packet_summary,
                mechanism_steps=[],
                rebuttal_note="",
                screenshots=[],
                assurance=assurance,
            )
            st.download_button(
                "Generate / download evidence packet draft",
                packet_bytes,
                file_name="elias_va_evidence_packet_draft.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.warning(f"Packet draft is unavailable right now: {exc}")

if not sources or not result:
    demo = (
        "The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
        "A later administrative review stated there was no evidence linking the current symptoms to service. "
        "A witness statement reported continuity of symptoms after training. "
        "The record may be incomplete because several service records were unavailable."
    )
    sources = [{"source_name": "Synthetic demo evidence", "page": 1, "text": demo}]
    result = audit_sources(sources)
    st.info("No uploaded record is active yet, so Elias is using a fictional demo record. Upload PDFs above to replace it for this session.")

st.markdown("#### How the workspaces fit together")
g1, g2, g3, g4 = st.columns(4, gap="small")
with g1:
    st.markdown('<div class="step-card"><b>1 · Elias</b><br><span class="micro">Start here. Load the record, ask questions, and create a first packet draft.</span></div>', unsafe_allow_html=True)
with g2:
    st.markdown('<div class="step-card"><b>2 · Review tools</b><br><span class="micro">Check provenance, quotations, packet integrity, and missing coverage in focused workspaces.</span></div>', unsafe_allow_html=True)
with g3:
    st.markdown('<div class="step-card"><b>3 · Floating Copilot</b><br><span class="micro">Use the ✦ button from review pages for quick source-grounded help without opening another workspace.</span></div>', unsafe_allow_html=True)
with g4:
    st.markdown('<div class="step-card"><b>4 · Human review</b><br><span class="micro">Verify source pages and conclusions before anything is submitted externally.</span></div>', unsafe_allow_html=True)

left, right = st.columns([2.15, 1], gap="large")

with right:
    st.markdown("### Voice Studio")
    st.markdown(
        """
        <div class="voice-card"><b>Default profile: Younger Distinguished</b><br>
        <span class="micro">Low-mid register, measured authority, crisp diction, slightly brighter/younger timbre, restrained warmth. The test uses your browser's available speech voices, so the exact sound varies by device.</span></div>
        """,
        unsafe_allow_html=True,
    )
    voice_profile = st.selectbox(
        "Voice profile",
        ["Younger Distinguished", "Command Briefing", "Calm Clinical"],
        index=0,
    )
    if voice_profile == "Younger Distinguished":
        rate, pitch = 0.94, 1.02
    elif voice_profile == "Command Briefing":
        rate, pitch = 0.90, 0.96
    else:
        rate, pitch = 0.91, 1.00
    st.caption("This is a synthetic voice direction, not a clone of a real speaker.")

    st.markdown("### Ask him to…")
    suggestions = [
        "What is the strongest evidence in this record?",
        "What record gaps should I resolve first?",
        "Show me the main adverse-versus-supporting tension.",
        "Which evidence best matches functional impact?",
    ]
    for suggestion in suggestions:
        if st.button(suggestion, use_container_width=True):
            st.session_state["elias_pending"] = suggestion

    st.markdown("### Current record")
    st.metric("Passages", len(result.get("items", [])))
    st.metric("Source/page units", result.get("source_count", 0))
    st.metric("Tension candidates", len(result.get("potential_contradictions", [])))

with left:
    if "elias_history" not in st.session_state:
        st.session_state["elias_history"] = [
            {
                "role": "assistant",
                "content": "Good. The record is loaded. Ask me for the strongest evidence, a specific issue, a contradiction, or what is still missing. I will stay close to the source and tell you when the record does not support a stronger conclusion.",
                "citations": [],
            }
        ]

    for message in st.session_state["elias_history"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            cites = message.get("citations") or []
            if cites:
                st.caption("Sources: " + " · ".join(dict.fromkeys(cites)))

    pending = st.session_state.pop("elias_pending", None)
    prompt = st.chat_input("Ask Elias about the evidence…")
    question = pending or prompt

    if question:
        st.session_state["elias_history"].append({"role": "user", "content": question, "citations": []})
        response = answer_question(question, result, sources)
        st.session_state["elias_history"].append(
            {"role": "assistant", "content": response["answer"], "citations": response.get("citations", [])}
        )
        st.rerun()

    latest = next((m for m in reversed(st.session_state["elias_history"]) if m["role"] == "assistant"), None)
    if latest:
        spoken = latest["content"]
        js_text = json.dumps(spoken)
        profile_label = html.escape(voice_profile)
        components.html(
            f"""
            <div style="font-family:Arial,sans-serif;border:1px solid #d6dbe6;border-radius:15px;padding:12px 14px;background:linear-gradient(135deg,#f8fbff,#f5fffd);display:flex;align-items:center;gap:12px;">
              <button id="speak" style="border:0;border-radius:999px;padding:10px 16px;background:#172b4d;color:white;font-weight:700;cursor:pointer;">▶ Speak as Elias</button>
              <button id="stop" style="border:1px solid #c7cfdd;border-radius:999px;padding:9px 13px;background:white;color:#24334f;font-weight:700;cursor:pointer;">Stop</button>
              <span style="font-size:12px;color:#65728a;">{profile_label} · browser voice preview</span>
            </div>
            <script>
              const text = {js_text};
              function chooseVoice() {{
                const voices = window.speechSynthesis.getVoices();
                const preferred = [/Ryan/i,/Guy/i,/Daniel/i,/David/i,/George/i,/Arthur/i,/Mark/i,/Male/i];
                for (const pattern of preferred) {{
                  const found = voices.find(v => /en[-_]/i.test(v.lang || '') && pattern.test(v.name || ''));
                  if (found) return found;
                }}
                return voices.find(v => /en[-_]/i.test(v.lang || '')) || voices[0] || null;
              }}
              document.getElementById('speak').onclick = () => {{
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                const voice = chooseVoice();
                if (voice) u.voice = voice;
                u.lang = 'en-US';
                u.rate = {rate};
                u.pitch = {pitch};
                u.volume = 1.0;
                window.speechSynthesis.speak(u);
              }};
              document.getElementById('stop').onclick = () => window.speechSynthesis.cancel();
              window.speechSynthesis.onvoiceschanged = () => chooseVoice();
            </script>
            """,
            height=72,
        )

st.divider()
st.caption(
    "Elias is a public-demo evidence assistant, not legal or medical counsel. Packet generation is an organizing aid, not a benefits determination. Source verification and human review remain required."
)
