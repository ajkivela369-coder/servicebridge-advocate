from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceClass(StrEnum):
    OFFICIAL_RECORD = "official_record"
    CLINICAL_RECORD = "clinical_record"
    MEDICAL_OPINION = "medical_opinion"
    LAY_STATEMENT = "lay_statement"
    CLAIMANT_REPORT = "claimant_report"
    LEGAL_AUTHORITY = "legal_authority"
    RESEARCH = "research"
    CORRESPONDENCE = "correspondence"
    UNKNOWN = "unknown"


class BenefitLane(StrEnum):
    VA_SERVICE_CONNECTION = "va_service_connection"
    VA_RATING = "va_rating"
    VA_TDIU_SMC = "va_tdiu_smc"
    SSDI_SSI = "ssdi_ssi"
    STATE_DISABILITY = "state_disability"
    EDUCATION_TPD = "education_tpd"
    ADA_504 = "ada_504"
    CLINICAL_ADVOCACY = "clinical_advocacy"
    GENERAL = "general"


class AdvocacyMode(StrEnum):
    PRIVATE_ANALYSIS = "private_analysis"
    EXTERNAL_DRAFT = "external_draft"


@dataclass(slots=True)
class SourceDocument:
    source_id: str
    title: str
    path: str
    evidence_class: EvidenceClass = EvidenceClass.UNKNOWN
    document_date: str | None = None
    author: str | None = None
    page_count: int | None = None
    sha256: str | None = None
    redacted: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_class"] = self.evidence_class.value
        return data


@dataclass(slots=True)
class EvidenceChunk:
    chunk_id: str
    source_id: str
    text: str
    ordinal: int
    locator: str | None = None
    evidence_class: EvidenceClass = EvidenceClass.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_class"] = self.evidence_class.value
        return data


@dataclass(slots=True)
class Citation:
    source_id: str
    title: str
    locator: str | None
    chunk_id: str
    evidence_class: EvidenceClass

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_class"] = self.evidence_class.value
        return data


@dataclass(slots=True)
class RetrievalHit:
    chunk: EvidenceChunk
    title: str
    score: float

    @property
    def citation(self) -> Citation:
        return Citation(
            source_id=self.chunk.source_id,
            title=self.title,
            locator=self.chunk.locator,
            chunk_id=self.chunk.chunk_id,
            evidence_class=self.chunk.evidence_class,
        )


@dataclass(slots=True)
class AdvocacyRequest:
    question: str
    lane: BenefitLane = BenefitLane.GENERAL
    mode: AdvocacyMode = AdvocacyMode.PRIVATE_ANALYSIS
    audience: str = "claimant"
    requested_output: str = "analysis"
    top_k: int = 8


@dataclass(slots=True)
class AdvocacyResponse:
    answer: str
    citations: list[Citation]
    retrieved_chunks: int
    model: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [citation.to_dict() for citation in self.citations],
            "retrieved_chunks": self.retrieved_chunks,
            "model": self.model,
            "warnings": self.warnings,
        }
