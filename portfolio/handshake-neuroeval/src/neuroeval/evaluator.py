from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable

HEDGE_WORDS = {"may", "might", "can", "could", "suggests", "associated", "likely", "approximately"}
CERTAINTY_WORDS = {"always", "never", "proves", "guarantees", "certainly", "definitely"}
MECHANISM_WORDS = {"because", "therefore", "via", "through", "causes", "results", "leads", "mechanism"}
EVIDENCE_WORDS = {"study", "evidence", "trial", "review", "data", "research", "observed"}

@dataclass(frozen=True)
class Evaluation:
    total: int
    factuality: int
    mechanism: int
    uncertainty: int
    evidence_language: int
    clarity: int
    flags: list[str]
    strengths: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z-]+", text.lower()))


def _bounded(value: int, low: int = 0, high: int = 5) -> int:
    return max(low, min(high, value))


def evaluate(answer: str, required_concepts: Iterable[str] = ()) -> Evaluation:
    """Score a biology/neuroscience answer on transparent reviewer-style dimensions."""
    text = answer.strip()
    tokens = _tokens(text)
    flags: list[str] = []
    strengths: list[str] = []

    concepts = [c.lower().strip() for c in required_concepts if c.strip()]
    matched = sum(1 for c in concepts if c in text.lower())
    factuality = 3 if not concepts else round(5 * matched / len(concepts))
    if concepts and matched == len(concepts):
        strengths.append("covers all required concepts")
    elif concepts:
        missing = [c for c in concepts if c not in text.lower()]
        flags.append("missing concepts: " + ", ".join(missing[:4]))

    mechanism = _bounded(2 + int(bool(tokens & MECHANISM_WORDS)) + int(len(text.split()) >= 35))
    if mechanism >= 4:
        strengths.append("explains a causal or mechanistic link")

    certainty_hits = sorted(tokens & CERTAINTY_WORDS)
    hedge_hits = tokens & HEDGE_WORDS
    uncertainty = _bounded(3 + int(bool(hedge_hits)) - min(2, len(certainty_hits)))
    if certainty_hits:
        flags.append("overconfident language: " + ", ".join(certainty_hits))
    elif hedge_hits:
        strengths.append("uses calibrated uncertainty")

    evidence_language = _bounded(2 + int(bool(tokens & EVIDENCE_WORDS)) + int("according to" in text.lower()))
    if evidence_language >= 3:
        strengths.append("signals evidence or source awareness")

    sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
    words = max(1, len(text.split()))
    avg_sentence = words / sentence_count
    clarity = 5 if 8 <= avg_sentence <= 28 else 3 if avg_sentence <= 40 else 2
    if words < 15:
        clarity = min(clarity, 3)
        flags.append("answer may be too brief to justify its conclusion")

    total = round((factuality * .35 + mechanism * .20 + uncertainty * .15 + evidence_language * .15 + clarity * .15) * 20)
    return Evaluation(total, factuality, mechanism, uncertainty, evidence_language, clarity, flags, strengths)
