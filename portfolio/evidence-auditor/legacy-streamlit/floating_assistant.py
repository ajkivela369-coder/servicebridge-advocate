from __future__ import annotations

import hashlib

import streamlit as st

from elias_memory import memory_context
from elias_plugins import default_plugin_state, respond


ELIAS_PARAM = "elias"


def workspace_signature(sources: list[dict] | None) -> str:
    digest = hashlib.sha256()
    for source in sources or []:
        digest.update(str(source.get("source_name") or "").encode("utf-8", errors="ignore"))
        digest.update(str(source.get("page") or "").encode("utf-8", errors="ignore"))
        digest.update((source.get("text") or "").encode("utf-8", errors="ignore"))
    return digest.hexdigest()[:12]


def _param_value(name: str) -> str | None:
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        try:
            value = st.experimental_get_query_params().get(name, [])
            return value[0] if value else None
        except Exception:
            return None


def _close_elias() -> None:
    try:
        if ELIAS_PARAM in st.query_params:
            del st.query_params[ELIAS_PARAM]
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
    st.rerun()


def _render_body(result: dict, sources: list[dict]) -> None:
    signature = workspace_signature(sources)
    if st.session_state.get("ea_quick_elias_signature") != signature:
        st.session_state["ea_quick_elias_signature"] = signature
        st.session_state["ea_quick_elias_history"] = []

    st.markdown("**Ask Elias**")
    st.caption("Quick evidence-grounded help without leaving this page. The full chat, case files, memory, and tools live in Elias.")

    if not sources or not result:
        st.info("No case record is loaded. Open Elias and add the case files first.")
        st.page_link("dashboard.py", label="Open Elias →", use_container_width=True)
        return

    history = st.session_state.setdefault("ea_quick_elias_history", [])
    for message in history[-6:]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("citations"):
                st.caption("Sources: " + " · ".join(dict.fromkeys(message["citations"])))

    question = st.text_input(
        "Ask about the loaded record",
        placeholder="Example: What is the strongest evidence on functional impact?",
        key="ea_quick_elias_question",
    )
    c1, c2 = st.columns([3, 1])
    send = c1.button("Ask Elias", type="primary", use_container_width=True, key="ea_quick_elias_send")
    clear = c2.button("Clear", use_container_width=True, key="ea_quick_elias_clear")
    if clear:
        st.session_state["ea_quick_elias_history"] = []
        st.rerun()
    if send and question.strip():
        plugins = st.session_state.get("elias_plugins") or default_plugin_state()
        response = respond(
            question.strip(),
            result,
            sources,
            plugins=plugins,
            memory_context=memory_context(st.session_state.get("elias_memory") or {}),
        )
        history.append({"role": "user", "content": question.strip(), "citations": []})
        history.append({"role": "assistant", "content": response.get("answer", ""), "citations": response.get("citations", [])})
        st.session_state["ea_quick_elias_history"] = history[-10:]
        st.rerun()

    st.divider()
    nav1, nav2 = st.columns(2)
    with nav1:
        st.page_link("dashboard.py", label="Open full Elias →", use_container_width=True)
    with nav2:
        if st.button("Close", use_container_width=True, key="ea_quick_elias_close"):
            _close_elias()

    st.caption("Session-local helper. Elias does not turn unsupported questions into guessed evidence.")


def render_floating_copilot(result: dict, sources: list[dict], *, enabled: bool = True) -> None:
    """Render a fixed Ask Elias launcher for reviewer pages.

    The historic function name remains for compatibility with page_copilot.py and older callers,
    but the user-facing experience is now Elias rather than a separate Copilot product surface.
    """
    if not enabled:
        return

    st.markdown(
        """
        <style>
        .ea-elias-fab{
          position:fixed;right:1.25rem;bottom:1.25rem;z-index:999999;
          width:58px;height:58px;border-radius:50%;display:flex;align-items:center;justify-content:center;
          text-decoration:none!important;font-size:1.15rem;font-weight:850;color:white!important;
          background:linear-gradient(145deg,#111827,#2563eb);border:1px solid rgba(255,255,255,.25);
          box-shadow:0 15px 38px rgba(15,23,42,.32);transition:transform .16s ease,box-shadow .16s ease;
        }
        .ea-elias-fab:hover{transform:translateY(-2px) scale(1.03);box-shadow:0 18px 45px rgba(15,23,42,.40)}
        .ea-elias-label{
          position:fixed;right:5.25rem;bottom:1.62rem;z-index:999998;padding:.38rem .62rem;border-radius:999px;
          background:rgba(15,23,42,.88);color:white;font-size:.72rem;font-weight:750;box-shadow:0 8px 24px rgba(15,23,42,.20);pointer-events:none;
        }
        @media(max-width:700px){.ea-elias-label{display:none}.ea-elias-fab{right:.85rem;bottom:.85rem}}
        </style>
        <span class="ea-elias-label">Ask Elias</span>
        <a class="ea-elias-fab" href="?elias=open" target="_self" title="Ask Elias" aria-label="Ask Elias">E</a>
        """,
        unsafe_allow_html=True,
    )

    if _param_value(ELIAS_PARAM) != "open":
        return

    if hasattr(st, "dialog"):
        dialog = st.dialog("Ask Elias", width="large")(_render_body)
        dialog(result, sources)
    else:
        with st.container(border=True):
            _render_body(result, sources)
