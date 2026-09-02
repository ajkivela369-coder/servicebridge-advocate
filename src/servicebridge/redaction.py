from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RedactionRule:
    name: str
    pattern: re.Pattern[str]
    replacement: str


RULES: tuple[RedactionRule, ...] = (
    RedactionRule(
        "ssn",
        re.compile(r"(?<!\d)(?!000|666|9\d\d)\d{3}[- ]?\d{2}[- ]?\d{4}(?!\d)"),
        "[REDACTED-SSN]",
    ),
    RedactionRule(
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[REDACTED-EMAIL]",
    ),
    RedactionRule(
        "phone",
        re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)"),
        "[REDACTED-PHONE]",
    ),
    RedactionRule(
        "dob_label",
        re.compile(
            r"\b(?:DOB|date of birth)\s*[:#-]?\s*(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b",
            re.IGNORECASE,
        ),
        "DOB: [REDACTED-DOB]",
    ),
    RedactionRule(
        "member_id",
        re.compile(r"\b(?:member|patient|claim|file)\s*(?:id|number|no\.?)[\s:#-]+[A-Z0-9-]{6,}\b", re.IGNORECASE),
        "[REDACTED-IDENTIFIER]",
    ),
)


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    """Redact high-risk identifiers and return counts by rule.

    This is a safety layer, not a guarantee of de-identification. Human review remains required.
    """

    counts: dict[str, int] = {}
    redacted = text
    for rule in RULES:
        redacted, count = rule.pattern.subn(rule.replacement, redacted)
        if count:
            counts[rule.name] = count
    return redacted, counts


def contains_unredacted_high_risk_identifier(text: str) -> bool:
    for rule in RULES:
        if rule.pattern.search(text):
            return True
    return False
