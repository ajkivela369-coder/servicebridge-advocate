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
    q = _tokens(question)
    scored: list[tuple[float, dict]] = []
    for item in result.get("items", []):
        text_tokens = _tokens(item.get("text", ""))
        issue_tokens = _tokens(" ".join(item.get("issues", [])))
        overlap = len(q & text_tokens) * 2.0 + len(q & issue_tokens) * 1.5
        stance_bonus = 0.35 if item.get("stance") in {"favorable", "mixed", "unfavorable"} else 0.0
        provenance_bonus = 0.25 if item.get("page") else 0.0
        score = overlap + stance_bonus + provenance_bonus + float(item.get("confidence", 0)) * 0.2
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if q:
        selected = [item for score, item in scored if score > 0.35][:limit]
        if selected:
            return selected
    return [item for _, item in scored[:limit]]


def answer_question(question: str, result: dict, sources: Sequence[dict] | None = None) -> dict:
    """Citation-first local helper for the public demo.

    This assistant is intentionally deterministic. It organizes the current audit and never claims to
    make a medical, legal, service-connection, or benefits determination.
    """
    question = (question or "").strip()
    lower = question.lower()
    sources = sources or []

    if not question:
        return {
            "answer": "Ask me about the strongest evidence, contradictions, source gaps, or a specific issue in the current review.",
            "citations": [],
            "mode": "orientation",
        }

    if any(term in lower for term in ("gap", "missing", "weak", "what is missing", "record problem")):
        flags = result.get("missing_record_flags", [])[:4]
        if not flags:
            answer = "I do not see a deterministic missing-record flag in the current material. That does not mean the record is complete; it means this screening pass did not detect one."
            return {"answer": answer, "citations": [], "mode": "record_gaps"}
        lines = ["The clearest record-completeness signals are:"]
        cites = []
        for flag in flags:
            locator = _locator(flag)
            lines.append(f"• {flag.get('text', '').strip()} — {locator}")
            cites.append(locator)
        lines.append("I would resolve these before treating the packet as complete.")
        return {"answer": "\n".join(lines), "citations": cites, "mode": "record_gaps"}

    if any(term in lower for term in ("contradiction", "rebuttal", "conflict", "opposing", "adverse")):
        tensions = result.get("potential_contradictions", [])[:3]
        if not tensions:
            return {
                "answer": "I do not see a same-issue cross-stance tension in the current screening result. I would still review source context before concluding the evidence is consistent.",
                "citations": [],
                "mode": "tensions",
            }
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
        return {"answer": "\n\n".join(blocks), "citations": cites, "mode": "tensions"}

    if any(term in lower for term in ("strongest", "best evidence", "most important", "top evidence")):
        favorable = [i for i in result.get("items", []) if i.get("stance") == "favorable"]
        favorable.sort(key=lambda item: (bool(item.get("page")), float(item.get("confidence", 0))), reverse=True)
        selected = favorable[:4] or _top_items(question, result, 4)
        intro = "These are the strongest source-locatable supporting passages in this screening pass:" if selected else "I do not have enough evidence loaded to rank supporting passages."
    else:
        selected = _top_items(question, result, 4)
        intro = "Here is the evidence in the current workspace that most directly matches your question:" if selected else "I do not have enough source material loaded to answer that from the record."

    lines = [intro]
    cites = []
    for item in selected:
        locator = _locator(item)
        stance = item.get("stance", "neutral").title()
        lines.append(f"• [{stance}] {item.get('text','').strip()} — {locator}")
        cites.append(locator)

    if selected:
        lines.append("I would verify each quoted passage in its original page context before using it externally.")
    return {"answer": "\n".join(lines), "citations": cites, "mode": "evidence_lookup"}
