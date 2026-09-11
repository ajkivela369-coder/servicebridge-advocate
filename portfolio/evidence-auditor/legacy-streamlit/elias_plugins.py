from __future__ import annotations

import re
from typing import Sequence

from copilot_engine import answer_question
from coverage import assess_issue_coverage
from packet_assurance import assess_packet_assurance
from quote_integrity import verify_quote_contextual
from readiness import assess_provenance_readiness

PLUGIN_CATALOG = {
    "record_search": {
        "label": "Record Search",
        "description": "Find source-backed passages that directly match the question.",
        "default": True,
    },
    "gap_finder": {
        "label": "Gap Finder",
        "description": "Surface missing-record signals and thin issue coverage.",
        "default": True,
    },
    "quote_check": {
        "label": "Quote Check",
        "description": "Verify proposed quotations against page-level source text.",
        "default": True,
    },
    "packet_assurance": {
        "label": "Packet Assurance",
        "description": "Check provenance, coverage depth, and quote integrity before handoff.",
        "default": True,
    },
}


def default_plugin_state() -> dict[str, bool]:
    return {name: bool(meta.get("default")) for name, meta in PLUGIN_CATALOG.items()}


def _extract_quoted_text(question: str) -> str:
    matches = re.findall(r'[“\"]([^”\"]{6,})[”\"]', question or "")
    return max(matches, key=len) if matches else ""


def respond(
    question: str,
    result: dict,
    sources: Sequence[dict],
    *,
    plugins: dict[str, bool] | None = None,
    memory_context: str = "",
) -> dict:
    """Route Elias through transparent local tools while preserving source-grounding."""
    plugins = plugins or default_plugin_state()
    q = (question or "").strip()
    lower = q.lower()
    tools_used: list[str] = []

    if any(term in lower for term in ("what do you remember", "memory", "remember about")):
        answer = memory_context or "Memory is off or no case memory has been set for this session."
        return {"answer": answer, "citations": [], "grounded": bool(memory_context), "mode": "memory", "tools_used": ["Case Memory"]}

    quoted = _extract_quoted_text(q)
    if quoted and plugins.get("quote_check", False):
        tools_used.append("Quote Check")
        check = verify_quote_contextual(quoted, sources)
        if check["status"] == "verified":
            locators = []
            for match in check.get("matches", [])[:4]:
                name = match.get("source_name", "Unknown source")
                page = match.get("page")
                locators.append(f"{name}, p. {page}" if page else name)
            return {
                "answer": "That quotation has a normalized exact match in the loaded record. Review its surrounding page context before using it externally.",
                "citations": locators,
                "grounded": True,
                "mode": "quote_check",
                "tools_used": tools_used,
            }
        return {
            "answer": check.get("note", "The proposed quotation could not be verified as exact."),
            "citations": [],
            "grounded": True,
            "mode": "quote_check",
            "tools_used": tools_used,
        }

    if any(term in lower for term in ("coverage", "thin support", "weakest issue", "develop the record")) and plugins.get("gap_finder", False):
        tools_used.append("Gap Finder")
        report = assess_issue_coverage(result.get("items", []))
        gaps = report.get("priority_gaps", [])[:5]
        if not gaps:
            return {
                "answer": "The current coverage screen did not identify a priority issue gap. That does not prove the record is complete.",
                "citations": [],
                "grounded": True,
                "mode": "coverage",
                "tools_used": tools_used,
            }
        lines = ["The first issues I would strengthen are:"]
        for gap in gaps:
            label = str(gap.get("issue", "unknown")).replace("_", " ").title()
            flags = " ".join(gap.get("flags", []))
            lines.append(f"• {label} — coverage {gap.get('coverage_score', 0)}/100. {flags}")
        return {"answer": "\n".join(lines), "citations": [], "grounded": True, "mode": "coverage", "tools_used": tools_used}

    if any(term in lower for term in ("packet ready", "ready to file", "assurance", "review ready")) and plugins.get("packet_assurance", False):
        tools_used.append("Packet Assurance")
        assurance = assess_packet_assurance(result.get("items", []), sources, [])
        lines = [
            f"Packet Assurance is {assurance['score']}/100 ({assurance['band'].replace('_', ' ')}).",
            f"Provenance {assurance['provenance_score']}/100 · coverage {assurance['coverage_score']}/100 · quote integrity {assurance['quote_score']}/100.",
        ]
        if assurance.get("blockers"):
            lines.append("Before handoff: " + " ".join(assurance["blockers"]))
        else:
            lines.append("No automated assurance blockers were found, but human source review is still required.")
        return {"answer": "\n".join(lines), "citations": [], "grounded": True, "mode": "assurance", "tools_used": tools_used}

    if plugins.get("record_search", True):
        tools_used.append("Record Search")
        base = answer_question(q, result, sources)
    else:
        base = {
            "answer": "Record Search is disabled. Turn it on in Elias Tools to answer source-grounded questions about the loaded record.",
            "citations": [],
            "grounded": False,
            "mode": "tool_disabled",
        }

    base["tools_used"] = tools_used
    return base


def plugin_snapshot(result: dict, sources: Sequence[dict]) -> dict:
    provenance = assess_provenance_readiness(sources)
    coverage = assess_issue_coverage(result.get("items", []))
    return {
        "provenance": provenance,
        "coverage": coverage,
    }
