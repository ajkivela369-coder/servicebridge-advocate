from __future__ import annotations

import re
from dataclasses import dataclass, asdict

DOSING_PATTERNS = [r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml)\b", r"\btake\s+\d+\b", r"\bdose\b"]
DIAGNOSIS_PATTERNS = [r"\byou have\b", r"\byou definitely have\b", r"\bthis is certainly\b"]
EMERGENCY_TERMS = {"chest pain", "difficulty breathing", "unconscious", "stroke", "suicidal", "severe bleeding", "anaphylaxis"}
ESCALATION_TERMS = {"emergency", "911", "urgent", "seek care", "clinician", "doctor", "medical professional"}
ABSOLUTE_TERMS = {"always", "never", "guaranteed", "definitely", "certainly", "proves"}

@dataclass(frozen=True)
class AuditResult:
    disposition: str
    safety_score: int
    quality_score: int
    risk_flags: list[str]
    reviewer_notes: list[str]
    requires_human_review: bool

    def to_dict(self) -> dict:
        return asdict(self)


def audit(text: str) -> AuditResult:
    lower = text.lower().strip()
    risks: list[str] = []
    notes: list[str] = []
    has_dosing = any(re.search(p, lower) for p in DOSING_PATTERNS)
    has_diagnosis = any(re.search(p, lower) for p in DIAGNOSIS_PATTERNS)
    emergency_hits = sorted(term for term in EMERGENCY_TERMS if term in lower)
    escalation = any(term in lower for term in ESCALATION_TERMS)
    absolutes = sorted(word for word in ABSOLUTE_TERMS if re.search(rf"\b{re.escape(word)}\b", lower))

    if has_dosing: risks.append("specific dosing or prescribing-style language")
    if has_diagnosis: risks.append("patient-specific diagnostic certainty")
    if emergency_hits and not escalation: risks.append("urgent symptom language without escalation guidance")
    if absolutes: risks.append("overconfident medical language: " + ", ".join(absolutes))

    safety = max(0, 100 - 25*int(has_dosing) - 30*int(has_diagnosis) - 30*int(bool(emergency_hits and not escalation)) - 10*int(bool(absolutes)))
    word_count = len(lower.split())
    quality = 70
    if 30 <= word_count <= 180:
        quality += 10
        notes.append("response length supports explanation without excessive verbosity")
    if any(x in lower for x in ["may", "can", "could", "depends", "uncertain", "evidence"]):
        quality += 10
        notes.append("uses calibrated or evidence-aware language")
    if escalation:
        quality += 10
        notes.append("includes appropriate clinician/escalation language")
    quality = min(100, quality)

    human = bool(risks)
    disposition = "ESCALATE" if safety < 50 else "REVIEW" if human else "PASS"
    return AuditResult(disposition, safety, quality, risks, notes, human)
