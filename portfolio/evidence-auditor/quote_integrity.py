from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Sequence


def _normalize(value: str) -> str:
    value = value.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def _sentences(value: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", value.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]


def _context(sentences: list[str], index: int, radius: int = 1) -> dict:
    return {
        "before": " ".join(sentences[max(0, index - radius):index]),
        "match": sentences[index] if 0 <= index < len(sentences) else "",
        "after": " ".join(sentences[index + 1:index + 1 + radius]),
    }


def _token_overlap(a: str, b: str) -> float:
    a_tokens = set(re.findall(r"\b\w+\b", _normalize(a)))
    b_tokens = set(re.findall(r"\b\w+\b", _normalize(b)))
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def _candidate_score(quote: str, candidate: str) -> float:
    q = _normalize(quote)
    c = _normalize(candidate)
    sequence = SequenceMatcher(None, q, c).ratio()
    overlap = _token_overlap(q, c)
    return round((0.65 * sequence) + (0.35 * overlap), 4)


def verify_quote_contextual(
    quote: str,
    sources: Sequence[dict],
    *,
    partial_threshold: float = 0.78,
) -> dict:
    """Verify a proposed quote and return source context without treating fuzzy matches as exact.

    Status meanings:
    - verified: normalized exact text exists in a source page.
    - partial: a similar sentence exists, but the quote is not exact and must not be presented as verbatim.
    - not_found: no sufficiently similar source sentence was found.
    """
    target = _normalize(quote)
    if not target:
        return {
            "status": "empty",
            "confidence": 0.0,
            "matches": [],
            "note": "Enter a quotation to verify.",
        }

    exact_matches = []
    partial_candidates = []

    for source in sources:
        raw_text = str(source.get("text", ""))
        normalized_text = _normalize(raw_text)
        sentences = _sentences(raw_text)
        source_name = source.get("source_name", "Unknown source")
        page = source.get("page")

        if target in normalized_text:
            sentence_index = next(
                (idx for idx, sentence in enumerate(sentences) if target in _normalize(sentence)),
                -1,
            )
            if sentence_index >= 0:
                context = _context(sentences, sentence_index)
            else:
                pos = normalized_text.find(target)
                context = {
                    "before": normalized_text[max(0, pos - 180):pos].strip(),
                    "match": target,
                    "after": normalized_text[pos + len(target):pos + len(target) + 180].strip(),
                }
            exact_matches.append(
                {
                    "source_name": source_name,
                    "page": page,
                    "match_type": "normalized_exact",
                    "score": 1.0,
                    "context": context,
                }
            )
            continue

        for idx, sentence in enumerate(sentences):
            score = _candidate_score(quote, sentence)
            partial_candidates.append(
                {
                    "source_name": source_name,
                    "page": page,
                    "match_type": "similar_not_exact",
                    "score": score,
                    "context": _context(sentences, idx),
                }
            )

    if exact_matches:
        return {
            "status": "verified",
            "confidence": 1.0,
            "matches": exact_matches,
            "note": "Normalized exact match found. Review the surrounding context before quoting externally.",
        }

    partial_candidates.sort(key=lambda item: item["score"], reverse=True)
    best = partial_candidates[0] if partial_candidates else None
    if best and best["score"] >= partial_threshold:
        return {
            "status": "partial",
            "confidence": best["score"],
            "matches": [best],
            "note": "Similar source language found, but it is not an exact quotation. Use the source wording or paraphrase it accurately.",
        }

    return {
        "status": "not_found",
        "confidence": best["score"] if best else 0.0,
        "matches": [best] if best else [],
        "note": "No exact or sufficiently similar source language was found. Do not present the proposed text as a verified quotation.",
    }
