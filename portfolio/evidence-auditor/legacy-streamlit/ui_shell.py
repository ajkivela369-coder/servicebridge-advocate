from __future__ import annotations

import streamlit as st


def render_app_nav(active: str = "elias") -> None:
    """Render a deliberately small three-destination navigation shell."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"]{display:none}
        [data-testid="stSidebar"]{border-right:1px solid rgba(120,130,150,.14)}
        .ea-nav-brand{font-weight:800;font-size:1.05rem;letter-spacing:-.01em;margin:.15rem 0 .15rem}
        .ea-nav-sub{font-size:.76rem;opacity:.58;line-height:1.35;margin-bottom:.75rem}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown('<div class="ea-nav-brand">Evidence Auditor Pro</div>', unsafe_allow_html=True)
        st.markdown('<div class="ea-nav-sub">Elias-first evidence workspace</div>', unsafe_allow_html=True)
        st.page_link("dashboard.py", label="Elias", icon="💬", use_container_width=True)
        st.page_link("pages/2_Case_Review.py", label="Case Review", icon="🔎", use_container_width=True)
        st.page_link("pages/3_Packet_Studio.py", label="Packet Studio", icon="📄", use_container_width=True)
        st.divider()


def workspace_status() -> tuple[list[dict], dict]:
    return st.session_state.get("ea_sources") or [], st.session_state.get("ea_result") or {}
