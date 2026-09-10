from __future__ import annotations

import re
from typing import Sequence

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "this", "that", "it", "as", "at", "by", "from", "what",
    "which", "who", "how", "my", "our", "your", "can", "could", "should", "would", "do",
}


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _locator(item: dict) -> str:
    source = item.get("source_name") or "Unknown source"
    page = item.get("page")
    return f"{source}, p. {page}" if page else source


def _top_items(question: str, result: dict, limit: int = 4) -> list[dict]:
    """Return only evidence with a meaningful lexical/issue match to the question.

    Earlier builds fell back to the highest-scoring evidence even when a non-empty question had no
    actual overlap. That made a superficially fluent answer possible without grounding. A non-empty
    question now returns no evidence when the record does not materially match it.
    """
    q = _tokens(question)
    scored: list[tuple[float, float, dict]] = []
    for item in result.get("items", []):
        text_tokens = _tokens(item.get("text", ""))
        issue_tokens = _tokens(" ".join(item.get("issues", [])))
        lexical_overlap = len(q & text_tokens) * 2.0 + len(q & issue_tokens) * 1.5
        stance_bonus = 0.35 if item.get("stance") in {"favorable", "mixed", "unfavorable"} else 0.0
        provenance_bonus = 0.25 if item.get("page") else 0.0
        score = lexical_overlap + stance_bonus + provenance_bonus + float(item.get("confidence", 0)) * 0.2
        scored.append((score, lexical_overlap, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    if q:
        return [item for _, lexical_overlap, item in scored if lexical_overlap > 0][:limit]
    return [item for _, _, item in scored[:limit]]


def _response(answer: str, citations: list[str], mode: str, *, grounded: bool) -> dict:
    return {
        "answer": answer,
        "citations": citations,
        "mode": mode,
        "grounded": grounded,
    }


def answer_question(question: str, result: dict, sources: Sequence[dict] | None = None) -> dict:
    """Citation-first deterministic helper used by the compact copilot and Elias.

    It organizes only the current audit. It does not infer facts that are absent from the record and
    never claims to make a medical, legal, service-connection, rating, or benefits determination.
    """
    question = (question or "").strip()
    lower = question.lower()
    sources = sources or []

    if not question:
        return _response(
            "Ask about the strongest evidence, contradictions, source gaps, a specific issue, or a quick record summary.",
            [],
            "orientation",
            grounded=False,
        )

    if any(term in lower for term in ("summary", "overview", "what is in the record", "record status")):
        summary = result.get("summary", {})
        issue_summary = result.get("issue_summary", {})
        top_issues = sorted(issue_summary.items(), key=lambda pair: (-pair[1], pair[0]))[:4]
        issue_text = ", ".join(f"{name.replace('_', ' ')} ({count})" for name, count in top_issues) or "none detected"
        answer = (
            f"This screening pass contains {len(result.get('items', []))} evidence passages across "
            f"{result.get('source_count', 0)} source/page units. It classified "
            f"{summary.get('favorable', 0)} favorable, {summary.get('unfavorable', 0)} unfavorable, "
            f"{summary.get('mixed', 0)} mixed, and {summary.get('neutral', 0)} neutral passages. "
            f"The most populated issue groups are: {issue_text}. There are "
            f"{len(result.get('potential_contradictions', []))} tension candidate(s) and "
            f"{len(result.get('missing_record_flags', []))} record-gap signal(s). "
            "These are routing counts, not findings about claim merit."
        )
        return _response(answer, [], "summary", grounded=True)

    if any(term in lower for term in ("gap", "missing", "weak", "what is missing", "record problem")):
        flags = result.get("missing_record_flags", [])[:4]
        if not flags:
            answer = (
                "I do not see a deterministic missing-record flag in the current material. That does not mean the "
                "record is complete; it means this screening pass did not detect one."
            )
            return _response(answer, [], "record_gaps", grounded=True)
        lines = ["The clearest record-completeness signals are:"]
        cites = []
        for flag in flags:
            locator = _locator(flag)
            lines.append(f"• {flag.get('text', '').strip()} — {locator}")
            cites.append(locator)
        lines.append("I would resolve these before treating the packet as complete.")
        return _response("\n".join(lines), cites, "record_gaps", grounded=True)

    if any(term in lower for term in ("contradiction", "rebuttal", "conflict", "opposing", "adverse")):
        tensions = result.get("potential_contradictions", [])[:3]
        if not tensions:
            return _response(
                "I do not see a same-issue cross-stance tension in the current screening result. That is not an automatic "
                "finding that the evidence is consistent; review the original source context before drawing that conclusion.",
                [],
                "tensions",
                grounded=True,
            )
        blocks = ["Here are the strongest tension pairs I would put on the review desk:"]
        cites = []
        for index, tension in enumerate(tensions, 1):
            fav = tension.get("favorable", {})
            unf = tension.get("unfavorable", {})
            issue = ", ".join(x.replace("_", " ") for x in tension.get("issues", [])) or "shared issue"
            blocks.append(
                f"{index}. {issue.title()}: supporting passage says “{fav.get('text','')}” ({_locator(fav)}); "
                f"the opposing passage says “{unf.get('text','')}” ({_locator(unf)})."
            )
            cites.extend([_locator(fav), _locator(unf)])
        blocks.append("That is a review target, not an automatic finding that either source is wrong.")
        return _response("\n\n".join(blocks), cites, "tensions", grounded=True)

    if any(term in lower for term in ("strongest", "best evidence", "most important", "top evidence")):
        favorable = [i for i in result.get("items", []) if i.get("stance") == "favorable"]
        favorable.sort(key=lambda item: (bool(item.get("page")), float(item.get("confidence", 0))), reverse=True)
        selected = favorable[:4]
        intro = (
            "These are the strongest source-locatable supporting passages in this screening pass:"
            if selected else
            "I do not have enough source-backed favorable evidence loaded to rank supporting passages."
        )
    else:
        selected = _top_items(question, result, 4)
        intro = "Here is the evidence in the current workspace that most directly matches your question:" if selected else ""

    if not selected:
        return _response(
            "I can't ground that question in the currently loaded evidence without guessing. Try naming an issue, source, "
            "symptom/function term, contradiction, or record gap—or open Elias for the full review workspace.",
            [],
            "unsupported",
            grounded=False,
        )

    lines = [intro]
    cites = []
    for item in selected:
        locator = _locator(item)
        stance = item.get("stance", "neutral").title()
        lines.append(f"• [{stance}] {item.get('text','').strip()} — {locator}")
        cites.append(locator)

    lines.append("Verify each quoted passage in its original page context before using it externally.")
    return _response("\n".join(lines), cites, "evidence_lookup", grounded=True)
