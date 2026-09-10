from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from assistant_bot import answer_question
from auditor import audit_sources


class EliasAssistantTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "source_name": "synthetic_exam.pdf",
                "page": 2,
                "text": "The clinician documented objective functional limitation during duty.",
            },
            {
                "source_name": "synthetic_review.pdf",
                "page": 5,
                "text": "The later review stated there was no evidence linking the symptoms to service.",
            },
            {
                "source_name": "synthetic_notice.pdf",
                "page": 1,
                "text": "Several service records were unavailable for review.",
            },
        ]
        self.result = audit_sources(self.sources)

    def test_evidence_lookup_preserves_source_locator(self):
        response = answer_question("What evidence supports functional impact?", self.result, self.sources)
        self.assertIn("synthetic_exam.pdf, p. 2", response["answer"])
        self.assertIn("synthetic_exam.pdf, p. 2", response["citations"])

    def test_gap_question_surfaces_missing_record_signal(self):
        response = answer_question("What records are missing?", self.result, self.sources)
        self.assertEqual(response["mode"], "record_gaps")
        self.assertIn("synthetic_notice.pdf, p. 1", response["answer"])

    def test_assistant_does_not_convert_tension_into_finding(self):
        response = answer_question("Show the contradiction", self.result, self.sources)
        self.assertEqual(response["mode"], "tensions")
        self.assertIn("not an automatic finding", response["answer"].lower())


if __name__ == "__main__":
    unittest.main()
