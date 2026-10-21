from servicebridge.data_quality import audit_source_quality, summarize_findings
from servicebridge.models import EvidenceClass, SourceDocument


def _source(**overrides):
    data = {
        "source_id": "src_demo",
        "title": "Synthetic record",
        "path": "/tmp/synthetic.txt",
        "evidence_class": EvidenceClass.CLINICAL_RECORD,
        "document_date": "2026-09-01",
        "sha256": "abc123",
        "redacted": True,
    }
    data.update(overrides)
    return SourceDocument(**data)


def test_clean_source_has_no_findings():
    assert audit_source_quality([_source()]) == []


def test_missing_metadata_is_reported_without_mutation():
    source = _source(
        evidence_class=EvidenceClass.UNKNOWN,
        document_date=None,
        sha256=None,
    )
    findings = audit_source_quality([source])
    codes = {item.code for item in findings}
    assert {"unknown_evidence_class", "missing_document_date", "missing_sha256"} <= codes
    assert source.document_date is None


def test_summary_counts_severity():
    findings = audit_source_quality([
        _source(evidence_class=EvidenceClass.UNKNOWN, document_date=None)
    ])
    summary = summarize_findings(findings)
    assert summary["warning"] == 1
    assert summary["info"] == 1
    assert summary["total"] == 2
