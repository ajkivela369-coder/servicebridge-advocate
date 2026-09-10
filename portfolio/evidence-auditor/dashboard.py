from __future__ import annotations

import hashlib
import sys
import uuid
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from auditor import audit_sources
from elias_memory import default_memory, export_memory, import_memory, memory_context, summarize_workspace
from elias_plugins import PLUGIN_CATALOG, default_plugin_state, respond
from ui_shell import render_app_nav

st.set_page_config(page_title="Elias · Evidence Auditor Pro", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"]{display:none}
    .block-container{max-width:980px;padding-top:.75rem;padding-bottom:7rem}
    .elias-top{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:.2rem 0 1.2rem}
    .elias-title{font-size:1.18rem;font-weight:780;letter-spacing:-.01em}
    .elias-pill{display:inline-flex;align-items:center;gap:.38rem;border:1px solid rgba(100,116,139,.22);border-radius:999px;padding:.3rem .62rem;font-size:.72rem;font-weight:700;opacity:.82}
    .elias-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px rgba(34,197,94,.65)}
    .welcome{padding:3.6rem .2rem 1.8rem;text-align:center}
    .welcome h1{font-size:2.05rem;letter-spacing:-.035em;margin:0 0 .55rem}
    .welcome p{max-width:650px;margin:0 auto;opacity:.68;line-height:1.55}
    .prompt-card{border:1px solid rgba(100,116,139,.18);border-radius:16px;padding:.85rem .95rem;min-height:104px;background:rgba(100,116,139,.025)}
    .prompt-card b{font-size:.86rem}.prompt-card span{display:block;font-size:.76rem;opacity:.62;line-height:1.4;margin-top:.3rem}
    .source-chip{display:inline-block;border:1px solid rgba(100,116,139,.20);border-radius:999px;padding:.2rem .48rem;margin:.12rem .12rem .12rem 0;font-size:.69rem;opacity:.74}
    .tool-chip{display:inline-block;border-radius:999px;padding:.18rem .45rem;margin:.08rem .12rem .08rem 0;font-size:.68rem;font-weight:700;background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.18)}
    .memory-card{border:1px solid rgba(100,116,139,.18);border-radius:14px;padding:.75rem .85rem;background:rgba(100,116,139,.025);font-size:.78rem;line-height:1.45}
    .composer-note{text-align:center;font-size:.68rem;opacity:.52;margin-top:.25rem}
    </style>
    """,
    unsafe_allow_html=True,
)


def _extract_sources(uploaded_files) -> list[dict]:
    sources: list[dict] = []
    for uploaded in uploaded_files or []:
        try:
            uploaded.seek(0)
            if uploaded.name.lower().endswith(".pdf"):
                reader = PdfReader(uploaded)
                for page_no, page in enumerate(reader.pages, 1):
                    text = (page.extract_text() or "").strip()
                    sources.append({"source_name": uploaded.name, "page": page_no, "text": text})
            else:
                raw = uploaded.getvalue().decode("utf-8", errors="replace")
                sources.append({"source_name": uploaded.name, "page": 1, "text": raw.strip()})
        except Exception as exc:
            st.warning(f"Could not read {uploaded.name}: {exc}")
    return sources


def _upload_signature(uploaded_files) -> str:
    digest = hashlib.sha256()
    for uploaded in uploaded_files or []:
        digest.update(uploaded.name.encode("utf-8", errors="ignore"))
        digest.update(str(getattr(uploaded, "size", 0)).encode())
    return digest.hexdigest()[:16]


def _new_thread() -> str:
    thread_id = uuid.uuid4().hex[:10]
    st.session_state.setdefault("elias_threads", {})[thread_id] = {
        "title": "New chat",
        "messages": [],
    }
    st.session_state["elias_active_thread"] = thread_id
    return thread_id


def _init_state() -> None:
    st.session_state.setdefault("elias_plugins", default_plugin_state())
    st.session_state.setdefault("elias_memory", default_memory())
    st.session_state.setdefault("elias_threads", {})
    if not st.session_state.get("elias_active_thread") or st.session_state["elias_active_thread"] not in st.session_state["elias_threads"]:
        _new_thread()


def _active_thread() -> dict:
    return st.session_state["elias_threads"][st.session_state["elias_active_thread"]]


def _set_thread_title(thread: dict, question: str) -> None:
    if thread.get("title") != "New chat":
        return
    compact = " ".join(question.strip().split())
    thread["title"] = compact[:42] + ("…" if len(compact) > 42 else "")


_init_state()
render_app_nav("elias")

with st.sidebar:
    if st.button("＋ New chat", use_container_width=True, type="primary"):
        _new_thread()
        st.rerun()

    st.markdown("**Chats**")
    for thread_id, thread in list(st.session_state["elias_threads"].items())[::-1]:
        label = thread.get("title") or "Untitled chat"
        if st.button(label, key=f"thread_{thread_id}", use_container_width=True):
            st.session_state["elias_active_thread"] = thread_id
            st.rerun()

    st.divider()
    st.markdown("**Case files**")
    uploads = st.file_uploader(
        "Add PDFs or text files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        key="elias_case_files",
        label_visibility="collapsed",
        help="Files are processed in the current Streamlit session. Public deployments should use fictional or de-identified records unless their data controls are appropriate for sensitive material.",
    )
    if uploads:
        signature = _upload_signature(uploads)
        if signature != st.session_state.get("elias_upload_signature"):
            extracted = _extract_sources(uploads)
            st.session_state["ea_sources"] = extracted
            st.session_state["ea_result"] = audit_sources(extracted)
            st.session_state["elias_upload_signature"] = signature
            memory = st.session_state["elias_memory"]
            memory["auto_summary"] = summarize_workspace(st.session_state["ea_result"], extracted)
            st.session_state["elias_memory"] = memory
            st.toast(f"Loaded {len(uploads)} file(s) into Elias.")

    sources = st.session_state.get("ea_sources") or []
    result = st.session_state.get("ea_result") or {}
    if sources:
        st.caption(f"{len(uploads or []) or len({s.get('source_name') for s in sources})} file(s) · {len(sources)} source/page units")
        if st.button("Clear case files", use_container_width=True):
            st.session_state["ea_sources"] = []
            st.session_state["ea_result"] = {}
            st.session_state.pop("elias_upload_signature", None)
            memory = st.session_state["elias_memory"]
            memory["auto_summary"] = "No case record loaded yet."
            st.session_state["elias_memory"] = memory
            st.rerun()
    else:
        st.caption("No case files loaded.")

    with st.expander("Memory", expanded=False):
        memory = st.session_state["elias_memory"]
        memory["enabled"] = st.toggle("Use case memory", value=bool(memory.get("enabled", True)), key="elias_memory_enabled")
        memory["case_label"] = st.text_input("Case label", value=memory.get("case_label", ""), placeholder="e.g., VA supplemental claim")
        memory["goal"] = st.text_area("Goal", value=memory.get("goal", ""), height=70, placeholder="What should Elias keep in mind?")
        memory["notes"] = st.text_area("Notes to remember", value=memory.get("notes", ""), height=95, placeholder="Stable context, terminology, or reviewer preferences")
        memory["auto_summary"] = summarize_workspace(result, sources)
        st.session_state["elias_memory"] = memory
        st.markdown(f'<div class="memory-card">{memory["auto_summary"]}</div>', unsafe_allow_html=True)
        st.caption("This demo memory is session-local. Export it if you want to carry the case context to another session.")
        st.download_button(
            "Export memory",
            export_memory(memory),
            file_name="elias_case_memory.json",
            mime="application/json",
            use_container_width=True,
        )
        memory_upload = st.file_uploader("Import memory JSON", type=["json"], key="elias_memory_import")
        if memory_upload is not None:
            try:
                imported = import_memory(memory_upload.getvalue().decode("utf-8"))
                imported["auto_summary"] = summarize_workspace(result, sources)
                st.session_state["elias_memory"] = imported
                st.success("Memory imported for this session.")
            except Exception as exc:
                st.error(f"Could not import memory: {exc}")

    with st.expander("Tools / plugins", expanded=False):
        st.caption("Built-in, local evidence tools. No external plugin account is connected in this public demo.")
        plugin_state = st.session_state["elias_plugins"]
        for name, meta in PLUGIN_CATALOG.items():
            plugin_state[name] = st.toggle(
                meta["label"],
                value=bool(plugin_state.get(name, meta.get("default", True))),
                key=f"plugin_{name}",
                help=meta["description"],
            )
        st.session_state["elias_plugins"] = plugin_state

    with st.expander("Response settings", expanded=False):
        st.session_state["elias_show_sources"] = st.toggle("Show source chips", value=st.session_state.get("elias_show_sources", True))
        st.session_state["elias_show_tools"] = st.toggle("Show tools used", value=st.session_state.get("elias_show_tools", True))
        st.caption("Elias remains evidence-grounded; these controls change presentation, not the underlying source boundary.")

    st.divider()
    st.caption("Public-safe baseline · human verification required")

sources = st.session_state.get("ea_sources") or []
result = st.session_state.get("ea_result") or {}
thread = _active_thread()

st.markdown(
    """
    <div class="elias-top">
      <div class="elias-title">Elias</div>
      <div class="elias-pill"><span class="elias-dot"></span> Evidence-grounded assistant</div>
    </div>
    """,
    unsafe_allow_html=True,
)

messages = thread.get("messages", [])
if not messages:
    st.markdown(
        """
        <div class="welcome">
          <h1>What are we working on?</h1>
          <p>Upload the record once, then talk to Elias naturally. He can search the evidence, surface gaps and contradictions, verify quotations, remember the case context for this session, and route the finished work into a reviewer packet.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards = [
        ("Find the strongest evidence", "Rank the most useful source-locatable supporting passages."),
        ("Stress-test the case", "Show adverse evidence, contradictions, and missing-record signals."),
        ("Explain the record", "Summarize a complicated issue in plain language without inventing facts."),
        ("Check packet readiness", "Review provenance and evidence coverage before handoff."),
    ]
    cols = st.columns(2, gap="small")
    for index, (title, desc) in enumerate(cards):
        with cols[index % 2]:
            st.markdown(f'<div class="prompt-card"><b>{title}</b><span>{desc}</span></div>', unsafe_allow_html=True)
            if st.button(title, key=f"starter_{index}", use_container_width=True):
                prompts = [
                    "What is the strongest evidence in this record?",
                    "Stress-test this case. What adverse evidence, contradictions, or missing records should I address?",
                    "Give me a clear summary of the current record and the main issues it supports.",
                    "Is this packet review-ready, and what should I fix first?",
                ]
                st.session_state["elias_pending_prompt"] = prompts[index]
                st.rerun()

for message in messages:
    with st.chat_message(message.get("role", "assistant")):
        st.markdown(message.get("content", ""))
        if message.get("role") == "assistant":
            if st.session_state.get("elias_show_sources", True) and message.get("citations"):
                chips = "".join(f'<span class="source-chip">{source}</span>' for source in dict.fromkeys(message["citations"]))
                st.markdown(chips, unsafe_allow_html=True)
            if st.session_state.get("elias_show_tools", True) and message.get("tools_used"):
                chips = "".join(f'<span class="tool-chip">{tool}</span>' for tool in message["tools_used"])
                st.markdown(chips, unsafe_allow_html=True)

if not sources:
    st.info("Upload case PDFs or text files in the left sidebar. Until then, Elias will not invent a case record.")

pending = st.session_state.pop("elias_pending_prompt", None)
prompt = st.chat_input("Message Elias")
question = pending or prompt

if question:
    _set_thread_title(thread, question)
    thread["messages"].append({"role": "user", "content": question})
    if not sources or not result:
        response = {
            "answer": "I don't have a case record loaded yet. Add the source documents in **Case files**, then ask me again. I won't manufacture evidence to fill the gap.",
            "citations": [],
            "grounded": False,
            "mode": "no_record",
            "tools_used": [],
        }
    else:
        response = respond(
            question,
            result,
            sources,
            plugins=st.session_state.get("elias_plugins") or {},
            memory_context=memory_context(st.session_state.get("elias_memory") or {}),
        )
    thread["messages"].append(
        {
            "role": "assistant",
            "content": response.get("answer", ""),
            "citations": response.get("citations", []),
            "tools_used": response.get("tools_used", []),
            "grounded": response.get("grounded", False),
            "mode": response.get("mode", ""),
        }
    )
    st.session_state["elias_threads"][st.session_state["elias_active_thread"]] = thread
    st.rerun()

st.markdown('<div class="composer-note">Elias can organize and draft from the loaded record, but source verification and human review remain required before external use.</div>', unsafe_allow_html=True)
