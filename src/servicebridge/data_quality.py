from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .models import SourceDocument


@dataclass(slots=True)
class SourceQualityFinding:
    source_id: str
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def audit_source_quality(sources: Iterable[SourceDocument]) -> list[SourceQualityFinding]:
    """Run deterministic metadata/provenance checks over indexed evidence sources.

    The audit never invents missing metadata and never changes a source. It only reports
    conditions that may reduce downstream traceability or retrieval confidence.
    """
    findings: list[SourceQualityFinding] = []
    seen_hashes: dict[str, str] = {}

    for source in sources:
        if source.evidence_class.value == "unknown":
            findings.append(
                SourceQualityFinding(
                    source.source_id,
                    "warning",
                    "unknown_evidence_class",
                    "Evidence class is unknown; downstream reasoning may lose source-type context.",
                )
            )

        if not source.document_date:
            findings.append(
                SourceQualityFinding(
                    source.source_id,
                    "info",
                    "missing_document_date",
                    "Document date is missing; chronology features may be less reliable.",
                )
            )

        if not source.sha256:
            findings.append(
                SourceQualityFinding(
                    source.source_id,
                    "warning",
                    "missing_sha256",
                    "Content hash is missing; duplicate and source-identity checks are weaker.",
                )
            )
        else:
            prior = seen_hashes.get(source.sha256)
            if prior and prior != source.source_id:
                findings.append(
                    SourceQualityFinding(
                        source.source_id,
                        "warning",
                        "duplicate_content_hash",
                        f"Content hash matches already indexed source {prior}.",
                    )
                )
            else:
                seen_hashes[source.sha256] = source.source_id

        if not source.title.strip():
            findings.append(
                SourceQualityFinding(
                    source.source_id,
                    "warning",
                    "missing_title",
                    "Source title is empty; human review and citation usability are reduced.",
                )
            )

        if not source.path:
            findings.append(
                SourceQualityFinding(
                    source.source_id,
                    "warning",
                    "missing_path",
                    "Original source path is missing; provenance tracing is reduced.",
                )
            )

    return findings


def summarize_findings(findings: Iterable[SourceQualityFinding]) -> dict[str, int]:
    summary = {"warning": 0, "info": 0}
    for finding in findings:
        summary[finding.severity] = summary.get(finding.severity, 0) + 1
    summary["total"] = sum(value for key, value in summary.items() if key != "total")
    return summary
