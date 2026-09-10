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

from assistant_bot import answer_question
from auditor import audit_sources

st.set_page_config(page_title="Elias · Evidence Assistant", page_icon="🛡️", layout="wide")

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
          <div class="elias-role">Evidence Auditor Pro · Human-guided assistant</div>
          <div class="elias-name">Elias</div>
          <div class="elias-copy">A calm, citation-first evidence companion. Elias helps you interrogate the record, surface the strongest source-backed passages, find gaps, and frame review questions without pretending to be the lawyer, clinician, or adjudicator.</div>
          <div class="status"><span class="dot"></span> Citation-first · source-locatable · human review required</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_r:
    st.markdown('<div class="portrait">E</div>', unsafe_allow_html=True)

sources = st.session_state.get("ea_sources")
result = st.session_state.get("ea_result")

if not sources or not result:
    with st.expander("Load PDFs directly into Elias", expanded=False):
        quick_files = st.file_uploader(
            "Source PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="elias_pdf_loader",
            help="For a public deployment, use fictional or thoroughly de-identified documents only.",
        )
        if quick_files:
            quick_sources = extract_pdf_sources(quick_files)
            if quick_sources:
                sources = quick_sources
                result = audit_sources(sources)
                st.session_state["ea_sources"] = sources
                st.session_state["ea_result"] = result
                st.success(f"Loaded {len(quick_files)} PDF(s) across {len(sources)} text-bearing pages.")

if not sources or not result:
    demo = (
        "The clinician documented objective functional limitation and stated that the condition was aggravated during duty. "
        "A later administrative review stated there was no evidence linking the current symptoms to service. "
        "A witness statement reported continuity of symptoms after training. "
        "The record may be incomplete because several service records were unavailable."
    )
    sources = [{"source_name": "Synthetic demo evidence", "page": 1, "text": demo}]
    result = audit_sources(sources)
    st.info("Elias is using the fictional demo record. Load PDFs above to test him against your own public-safe/de-identified material.")

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
    st.caption("This is a new synthetic voice direction, not a clone of the speaker in the reference video.")

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
    "Elias is a public-demo evidence assistant, not a person and not legal or medical counsel. "
    "His voice preview uses browser speech synthesis and intentionally does not clone a real speaker."
)
