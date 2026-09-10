from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from auditor import audit_sources
from packet_assurance import assess_packet_assurance


class PacketAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {"source_name": "synthetic_exam.pdf", "page": 2, "text": "The clinician documented objective functional limitation during duty."},
            {"source_name": "synthetic_followup.pdf", "page": 4, "text": "A follow-up note documented continued functional limitation and restricted activity."},
        ]
        self.result = audit_sources(self.sources)

    def test_verified_quote_preserves_high_quote_integrity(self):
        report = assess_packet_assurance(
            self.result["items"],
            self.sources,
            ["The clinician documented objective functional limitation during duty."],
        )
        self.assertEqual(report["quote_score"], 100)
        self.assertEqual(report["quotes"]["unresolved"], 0)

    def test_unverified_quote_creates_blocker(self):
        report = assess_packet_assurance(
            self.result["items"],
            self.sources,
            ["A physician definitively attributed the condition to service."],
        )
        self.assertGreater(report["quotes"]["unresolved"], 0)
        self.assertTrue(any("verbatim quote" in blocker.lower() for blocker in report["blockers"]))

    def test_thin_issue_reduces_readiness(self):
        one_source = [{"source_name": "synthetic_exam.pdf", "page": 2, "text": "The clinician documented objective functional limitation during duty."}]
        one_result = audit_sources(one_source)
        report = assess_packet_assurance(one_result["items"], one_source, [])
        self.assertGreaterEqual(report["coverage"]["thin"], 1)
        self.assertEqual(report["band"], "needs_review")


if __name__ == "__main__":
    unittest.main()
