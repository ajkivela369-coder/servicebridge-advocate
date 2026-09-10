from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from auditor import audit_sources
from coverage import assess_issue_coverage
from packet_assurance import assess_packet_assurance
from packet_builder import build_packet


class PacketBuilderAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "source_name": "synthetic_exam.pdf",
                "page": 2,
                "text": "The clinician documented objective functional limitation during duty.",
            },
            {
                "source_name": "synthetic_followup.pdf",
                "page": 4,
                "text": "A follow-up note documented continued functional limitation and restricted activity.",
            },
        ]
        self.result = audit_sources(self.sources)

    @staticmethod
    def pdf_text(payload: bytes) -> str:
        reader = PdfReader(BytesIO(payload))
        # PDF extractors may insert line breaks at layout boundaries. Normalize whitespace so
        # assertions test document semantics rather than ReportLab's wrapping decisions.
        raw = "\n".join((page.extract_text() or "") for page in reader.pages)
        return " ".join(raw.split())

    def test_assurance_summary_is_embedded_with_verified_quote_locator(self):
        assurance = assess_packet_assurance(
            self.result["items"],
            self.sources,
            ["The clinician documented objective functional limitation during duty."],
        )
        payload = build_packet(
            self.result,
            case_title="Synthetic Demonstration Case",
            assurance=assurance,
        )
        text = self.pdf_text(payload)
        self.assertIn("Reviewer Assurance Summary", text)
        self.assertIn("Quote Verification Register", text)
        self.assertIn("synthetic_exam.pdf, p. 2", text)
        self.assertIn("not a legal, medical", text)

    def test_unresolved_quote_is_visible_in_exported_register(self):
        assurance = assess_packet_assurance(
            self.result["items"],
            self.sources,
            ["A physician definitively attributed the condition to service."],
        )
        payload = build_packet(self.result, assurance=assurance)
        text = self.pdf_text(payload)
        self.assertIn("Reviewer blockers", text)
        self.assertIn("Not Found", text)
        self.assertIn("No verified source locator", text)
        self.assertNotIn("A physician definitively attributed the condition to service. Not Found synthetic_exam.pdf, p. 2", text)

    def test_priority_gap_keeps_its_actual_coverage_band_in_pdf(self):
        # Two locatable passages + one source type yield a developing score, while the
        # single-source/diversity flags keep the issue in priority_gaps for the PDF table.
        items = [
            {
                "evidence_id": "E1",
                "source_name": "synthetic_single_source.pdf",
                "page": 1,
                "text": "Functional limitation was documented.",
                "issues": ["functional_impact"],
                "source_type": "medical",
                "stance": "favorable",
            },
            {
                "evidence_id": "E2",
                "source_name": "synthetic_single_source.pdf",
                "page": 2,
                "text": "Restricted activity continued.",
                "issues": ["functional_impact"],
                "source_type": "medical",
                "stance": "favorable",
            },
        ]
        coverage = assess_issue_coverage(items)
        gap = coverage["priority_gaps"][0]
        self.assertEqual(gap["coverage_band"], "developing")
        self.assertEqual(gap["band"], "developing")

        assurance = {
            "score": 70,
            "band": "review_ready_with_cautions",
            "provenance_score": 90,
            "coverage_score": gap["coverage_score"],
            "quote_score": 100,
            "blockers": [],
            "coverage": coverage,
            "quotes": {"results": []},
        }
        result = {
            "summary": {"favorable": 2, "unfavorable": 0, "mixed": 0, "neutral": 0},
            "source_count": 2,
            "potential_contradictions": [],
            "issue_summary": {"functional_impact": 2},
            "items": items,
        }
        text = self.pdf_text(build_packet(result, assurance=assurance))
        self.assertIn("Functional Impact", text)
        self.assertIn("Developing", text)

    def test_existing_packet_generation_remains_backward_compatible(self):
        payload = build_packet(self.result, case_title="Legacy Compatible Packet")
        text = self.pdf_text(payload)
        self.assertIn("Legacy Compatible Packet", text)
        self.assertNotIn("Reviewer Assurance Summary", text)


if __name__ == "__main__":
    unittest.main()
