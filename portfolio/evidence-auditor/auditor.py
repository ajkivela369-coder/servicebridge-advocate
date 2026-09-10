from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable


FAVORABLE_TERMS = {
    "supports", "consistent with", "at least as likely", "aggravated", "worsened",
    "functional limitation", "unable", "credible", "objective", "documented",
    "service", "duty", "onset", "continuity", "nexus", "positive opinion"
}

UNFAVORABLE_TERMS = {
    "less likely", "not related", "no evidence", "normal examination", "resolved",
    "preexisting without aggravation", "negative opinion", "inconsistent", "denied"
}

SOURCE_HINTS = {
    "medical": ["exam", "dbq", "physician", "clinician", "treatment", "diagnosis", "imaging", "emg"],
    "service": ["orders", "duty", "drill", "training", "line of duty", "service record", "unit"],
    "lay": ["statement", "witness", "buddy", "family", "self-report", "reported"],
    "administrative": ["decision", "rating", "appeal", "review", "notice", "claim"]
}


@dataclass
class EvidenceItem:
    text: str
    stance: str
    source_type: str
    confidence: float
    rationale: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]


def _contains_any(text: str, terms: Iterable[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term in lower]


def infer_source_type(text: str) -> str:
    lower = text.lower()
    scores = {
        source: sum(1 for hint in hints if hint in lower)
        for source, hints in SOURCE_HINTS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unspecified"


def classify_sentence(sentence: str) -> EvidenceItem:
    favorable = _contains_any(sentence, FAVORABLE_TERMS)
    unfavorable = _contains_any(sentence, UNFAVORABLE_TERMS)
    rationale: list[str] = []

    if favorable:
        rationale.append("Favorable indicators: " + ", ".join(favorable[:4]))
    if unfavorable:
        rationale.append("Unfavorable indicators: " + ", ".join(unfavorable[:4]))

    if favorable and unfavorable:
        stance = "mixed"
        confidence = 0.60
    elif favorable:
        stance = "favorable"
        confidence = min(0.95, 0.62 + 0.07 * len(favorable))
    elif unfavorable:
        stance = "unfavorable"
        confidence = min(0.95, 0.62 + 0.07 * len(unfavorable))
    else:
        stance = "neutral"
        confidence = 0.45
        rationale.append("No deterministic stance phrase detected.")

    if re.search(r"\b(may|might|could|possibly|unclear|uncertain)\b", sentence.lower()):
        rationale.append("Uncertainty language detected.")
        confidence = max(0.35, confidence - 0.10)

    return EvidenceItem(
        text=sentence,
        stance=stance,
        source_type=infer_source_type(sentence),
        confidence=round(confidence, 2),
        rationale=rationale,
    )


def audit_text(text: str) -> dict:
    items = [classify_sentence(s) for s in _sentences(text)]
    counts = {k: 0 for k in ["favorable", "unfavorable", "mixed", "neutral"]}
    for item in items:
        counts[item.stance] += 1

    contradictions = []
    favorable_text = " ".join(i.text.lower() for i in items if i.stance == "favorable")
    unfavorable_text = " ".join(i.text.lower() for i in items if i.stance == "unfavorable")
    shared = sorted({w for w in re.findall(r"\b[a-z]{6,}\b", favorable_text)} & {w for w in re.findall(r"\b[a-z]{6,}\b", unfavorable_text)})
    if shared:
        contradictions.append({
            "type": "potential_cross-document_tension",
            "shared_terms": shared[:8],
            "note": "Favorable and unfavorable passages discuss overlapping concepts; human review is recommended."
        })

    return {
        "summary": counts,
        "items": [i.to_dict() for i in items],
        "potential_contradictions": contradictions,
        "review_note": "Deterministic screening only. Verify every conclusion against the underlying source and governing rules."
    }
