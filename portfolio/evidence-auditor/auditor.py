from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable, Sequence

FAVORABLE_TERMS = {
    "supports", "consistent with", "at least as likely", "aggravated", "worsened",
    "functional limitation", "unable", "credible", "objective", "documented",
    "service", "duty", "onset", "continuity", "nexus", "positive opinion",
}
UNFAVORABLE_TERMS = {
    "less likely", "not related", "no evidence", "normal examination", "resolved",
    "preexisting without aggravation", "negative opinion", "inconsistent", "denied",
}
SOURCE_HINTS = {
    "medical": ["exam", "dbq", "physician", "clinician", "treatment", "diagnosis", "imaging", "emg"],
    "service": ["orders", "duty", "drill", "training", "line of duty", "service record", "unit"],
    "lay": ["statement", "witness", "buddy", "family", "self-report", "reported"],
    "administrative": ["decision", "rating", "appeal", "review", "notice", "claim"],
}
ISSUE_HINTS = {
    "service_connection": ["service", "duty", "drill", "training", "line of duty", "nexus"],
    "aggravation": ["aggravated", "worsened", "preexisting", "flare", "reinjury"],
    "functional_impact": ["functional limitation", "unable", "work", "occupational", "daily activities"],
    "continuity": ["continuity", "since", "ongoing", "persistent", "after training"],
    "objective_findings": ["objective", "imaging", "emg", "exam", "test", "documented"],
    "record_completeness": ["missing", "unavailable", "incomplete", "not obtained", "unable to locate"],
}
MISSING_RECORD_HINTS = [
    "unavailable", "missing", "not found", "incomplete", "not obtained",
    "unable to locate", "records were unavailable",
]


@dataclass
class EvidenceItem:
    text: str
    stance: str
    source_type: str
    confidence: float
    issues: list[str]
    rationale: list[str]
    source_name: str = "Pasted evidence"
    page: int | None = None
    evidence_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()] if cleaned else []


def _contains_any(text: str, terms: Iterable[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term in lower]


def infer_source_type(text: str) -> str:
    lower = text.lower()
    scores = {source: sum(h in lower for h in hints) for source, hints in SOURCE_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "unspecified"


def infer_issues(text: str) -> list[str]:
    lower = text.lower()
    return [issue for issue, hints in ISSUE_HINTS.items() if any(h in lower for h in hints)] or ["general_evidence"]


def classify_sentence(
    sentence: str,
    *,
    source_name: str = "Pasted evidence",
    page: int | None = None,
    evidence_id: str = "",
) -> EvidenceItem:
    favorable = _contains_any(sentence, FAVORABLE_TERMS)
    unfavorable = _contains_any(sentence, UNFAVORABLE_TERMS)
    rationale: list[str] = []
    if favorable:
        rationale.append("Favorable indicators: " + ", ".join(favorable[:4]))
    if unfavorable:
        rationale.append("Unfavorable indicators: " + ", ".join(unfavorable[:4]))

    if favorable and unfavorable:
        stance, confidence = "mixed", 0.60
    elif favorable:
        stance, confidence = "favorable", min(0.95, 0.62 + 0.07 * len(favorable))
    elif unfavorable:
        stance, confidence = "unfavorable", min(0.95, 0.62 + 0.07 * len(unfavorable))
    else:
        stance, confidence = "neutral", 0.45
        rationale.append("No deterministic stance phrase detected.")

    if re.search(r"\b(may|might|could|possibly|unclear|uncertain)\b", sentence.lower()):
        rationale.append("Uncertainty language detected.")
        confidence = max(0.35, confidence - 0.10)

    return EvidenceItem(
        sentence,
        stance,
        infer_source_type(sentence),
        round(confidence, 2),
        infer_issues(sentence),
        rationale,
        source_name,
        page,
        evidence_id,
    )


def _normalize_quote(value: str) -> str:
    value = value.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def verify_quote(quote: str, sources: Sequence[dict]) -> dict:
    """Verify a quote against source-page text using exact and normalized matching."""
    target = _normalize_quote(quote)
    if not target:
        return {"status": "empty", "matches": [], "note": "Enter a quotation to verify."}

    matches = []
    for source in sources:
        haystack = _normalize_quote(str(source.get("text", "")))
        if target in haystack:
            matches.append(
                {
                    "source_name": source.get("source_name", "Unknown source"),
                    "page": source.get("page"),
                    "match_type": "normalized_exact",
                }
            )
    return {
        "status": "verified" if matches else "not_found",
        "matches": matches,
        "note": (
            "Quote matched source-page text after whitespace/punctuation normalization."
            if matches
            else "No exact normalized match found. Human review is required before using the quotation."
        ),
    }


def audit_sources(sources: Sequence[dict]) -> dict:
    items: list[EvidenceItem] = []
    counter = 1
    for source in sources:
        source_name = str(source.get("source_name") or "Unknown source")
        page = source.get("page")
        for sentence in _sentences(str(source.get("text", ""))):
            items.append(
                classify_sentence(
                    sentence,
                    source_name=source_name,
                    page=page,
                    evidence_id=f"E-{counter:04d}",
                )
            )
            counter += 1

    counts = {k: sum(i.stance == k for i in items) for k in ["favorable", "unfavorable", "mixed", "neutral"]}
    issue_counts: dict[str, int] = {}
    for item in items:
        for issue in item.issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    missing_records = [
        {
            "evidence_id": i.evidence_id,
            "source_name": i.source_name,
            "page": i.page,
            "text": i.text,
        }
        for i in items
        if any(h in i.text.lower() for h in MISSING_RECORD_HINTS)
    ]

    contradictions = []
    favorable_items = [i for i in items if i.stance == "favorable"]
    unfavorable_items = [i for i in items if i.stance == "unfavorable"]
    for fav in favorable_items:
        for unfav in unfavorable_items:
            shared_issues = sorted(set(fav.issues) & set(unfav.issues) - {"general_evidence"})
            if shared_issues:
                contradictions.append(
                    {
                        "type": "cross_stance_issue_tension",
                        "issues": shared_issues,
                        "favorable": fav.to_dict(),
                        "unfavorable": unfav.to_dict(),
                        "note": "Opposing passages address the same issue; human reconciliation is recommended.",
                    }
                )

    matrix = [
        {
            "evidence_id": i.evidence_id,
            "stance": i.stance,
            "source_type": i.source_type,
            "source_name": i.source_name,
            "page": i.page,
            "issues": ", ".join(i.issues),
            "confidence": i.confidence,
            "passage": i.text,
        }
        for i in items
    ]
    return {
        "summary": counts,
        "issue_summary": issue_counts,
        "items": [i.to_dict() for i in items],
        "evidence_matrix": matrix,
        "potential_contradictions": contradictions,
        "missing_record_flags": missing_records,
        "source_count": len({(s.get("source_name"), s.get("page")) for s in sources}),
        "review_note": "Deterministic screening only. Verify every conclusion against the underlying source and governing rules.",
    }


def audit_text(text: str) -> dict:
    return audit_sources([{"source_name": "Pasted evidence", "page": None, "text": text}])
