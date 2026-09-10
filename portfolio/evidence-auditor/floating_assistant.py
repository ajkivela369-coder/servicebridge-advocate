from __future__ import annotations

import hashlib

import streamlit as st

from assistant_bot import answer_question


COPILOT_PARAM = "copilot"


def workspace_signature(sources: list[dict] | None) -> str:
    """Return a short session-only signature so chat resets when the loaded record changes."""
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


def _close_copilot() -> None:
    try:
        if COPILOT_PARAM in st.query_params:
            del st.query_params[COPILOT_PARAM]
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
    st.rerun()


def _render_body(result: dict, sources: list[dict]) -> None:
    signature = workspace_signature(sources)
    if st.session_state.get("ea_copilot_signature") != signature:
        st.session_state["ea_copilot_signature"] = signature
        st.session_state["ea_copilot_history"] = []

    st.markdown("**Evidence Copilot**")
    st.caption(
        "A compact, source-grounded helper for quick questions while you work. "
        "Elias remains the separate full evidence-assistant workspace."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Passages", len(result.get("items", [])))
    c2.metric("Source/page units", result.get("source_count", 0))
    c3.metric("Tensions", len(result.get("potential_contradictions", [])))

    suggestions = [
        "Give me a quick record summary",
        "What is the strongest evidence?",
        "What records look missing?",
        "Show the main contradiction",
    ]
    picked = st.selectbox("Quick ask", ["Choose a prompt…"] + suggestions, key="ea_copilot_quick")

    history = st.session_state.setdefault("ea_copilot_history", [])
    for message in history[-4:]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("citations"):
                st.caption("Sources: " + " · ".join(dict.fromkeys(message["citations"])))

    question = st.text_input(
        "Ask about the loaded evidence",
        placeholder="Example: What evidence mentions functional impact?",
        key="ea_copilot_question",
    )
    send_col, clear_col = st.columns([3, 1])
    send = send_col.button("Ask Copilot", use_container_width=True, type="primary")
    clear = clear_col.button("Clear", use_container_width=True)

    if clear:
        st.session_state["ea_copilot_history"] = []
        st.rerun()

    submitted = question.strip() if send else ""
    if picked != "Choose a prompt…" and not submitted:
        submitted = picked

    if submitted:
        response = answer_question(submitted, result, sources)
        history.append({"role": "user", "content": submitted, "citations": []})
        history.append(
            {
                "role": "assistant",
                "content": response["answer"],
                "citations": response.get("citations", []),
                "grounded": response.get("grounded", False),
            }
        )
        st.session_state["ea_copilot_history"] = history[-8:]
        st.session_state["ea_copilot_quick"] = "Choose a prompt…"
        st.session_state["ea_copilot_question"] = ""
        st.rerun()

    st.divider()
    link_col, close_col = st.columns([2, 1])
    with link_col:
        try:
            st.page_link("pages/6_Elias_Assistant.py", label="Open Elias full workspace →")
        except Exception:
            st.caption("Use the app navigation to open Elias for the full assistant workspace.")
    with close_col:
        if st.button("Close", use_container_width=True, key="ea_copilot_close"):
            _close_copilot()

    st.caption(
        "Session-local helper. It does not save the loaded record, make legal/medical findings, or turn an unsupported question into a guessed answer."
    )


def render_floating_copilot(result: dict, sources: list[dict], *, enabled: bool = True) -> None:
    """Render a fixed launcher and a modal/inline compact evidence copilot.

    The launcher is plain HTML for stable fixed positioning. The actual assistant remains native
    Streamlit UI so questions and evidence never need to be sent to a third-party widget.
    """
    if not enabled:
        return

    st.markdown(
        """
        <style>
        .ea-copilot-fab{
          position:fixed;right:1.35rem;bottom:1.35rem;z-index:999999;
          width:58px;height:58px;border-radius:50%;display:flex;align-items:center;justify-content:center;
          text-decoration:none!important;font-size:1.45rem;font-weight:900;color:white!important;
          background:linear-gradient(145deg,#2563eb,#0f766e);border:1px solid rgba(255,255,255,.28);
          box-shadow:0 15px 38px rgba(15,23,42,.34);transition:transform .16s ease,box-shadow .16s ease;
        }
        .ea-copilot-fab:hover{transform:translateY(-2px) scale(1.03);box-shadow:0 18px 45px rgba(15,23,42,.42)}
        .ea-copilot-label{
          position:fixed;right:5.35rem;bottom:1.72rem;z-index:999998;padding:.38rem .62rem;border-radius:999px;
          background:rgba(15,23,42,.88);color:white;font-size:.72rem;font-weight:750;letter-spacing:.02em;
          box-shadow:0 8px 24px rgba(15,23,42,.20);pointer-events:none;
        }
        @media(max-width:700px){.ea-copilot-label{display:none}.ea-copilot-fab{right:.9rem;bottom:.9rem}}
        </style>
        <span class="ea-copilot-label">Evidence Copilot</span>
        <a class="ea-copilot-fab" href="?copilot=open" target="_self" title="Open Evidence Copilot" aria-label="Open Evidence Copilot">✦</a>
        """,
        unsafe_allow_html=True,
    )

    if _param_value(COPILOT_PARAM) != "open":
        return

    if hasattr(st, "dialog"):
        dialog = st.dialog("Evidence Copilot", width="large")(_render_body)
        dialog(result, sources)
    else:
        st.warning("Floating modal is unavailable in this Streamlit version; showing the Copilot inline instead.")
        with st.container(border=True):
            _render_body(result, sources)
