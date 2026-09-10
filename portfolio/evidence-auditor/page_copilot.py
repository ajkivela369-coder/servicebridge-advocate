from __future__ import annotations

import streamlit as st

from auditor import audit_sources
from floating_assistant import render_floating_copilot


def resolve_copilot_context(
    *,
    sources: list[dict] | None = None,
    result: dict | None = None,
) -> tuple[dict, list[dict]]:
    """Resolve the best evidence context for a reviewer page without persisting new data.

    Page-local evidence wins when supplied. Otherwise the Copilot reuses the main Evidence Auditor
    session workspace. Nothing here uploads, writes, or saves evidence.
    """
    session_sources = st.session_state.get("ea_sources") or []
    active_sources = list(sources) if sources else list(session_sources)

    if result is not None:
        active_result = result
    elif active_sources:
        active_result = audit_sources(active_sources)
    else:
        active_result = {
            "items": [],
            "summary": {"favorable": 0, "unfavorable": 0, "mixed": 0, "neutral": 0},
            "issue_summary": {},
            "source_count": 0,
            "potential_contradictions": [],
            "missing_record_flags": [],
        }

    return active_result, active_sources


def render_page_copilot(
    *,
    sources: list[dict] | None = None,
    result: dict | None = None,
    enabled: bool = True,
) -> None:
    """Render the persistent floating Evidence Copilot on a reviewer tool page."""
    active_result, active_sources = resolve_copilot_context(sources=sources, result=result)
    render_floating_copilot(active_result, active_sources, enabled=enabled)
