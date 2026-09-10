from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from packet_guard import audit_packet_quotes


class PacketGuardTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "source_name": "synthetic_exam.pdf",
                "page": 4,
                "text": (
                    "The clinician documented objective functional limitation and stated "
                    "that the condition was aggravated during duty. A later review requested "
                    "additional records."
                ),
            }
        ]

    def test_exact_quote_passes_gate(self):
        report = audit_packet_quotes(
            ["The clinician documented objective functional limitation and stated that the condition was aggravated during duty."],
            self.sources,
        )
        self.assertTrue(report["export_ready"])
        self.assertEqual(report["counts"]["verified"], 1)
        self.assertEqual(report["results"][0]["matches"][0]["page"], 4)
        self.assertEqual(report["results"][0]["candidate_matches"], [])

    def test_unverified_quote_blocks_gate(self):
        report = audit_packet_quotes(
            ["The clinician proved the condition was permanently caused by duty."],
            self.sources,
        )
        self.assertFalse(report["export_ready"])
        self.assertGreater(report["unresolved"], 0)
        item = report["results"][0]
        self.assertEqual(item["matches"], [])
        # Similarity candidates may be retained for human comparison, but are never
        # exposed through the verified-match field used by packet provenance.
        self.assertIn("candidate_matches", item)

    def test_mixed_register_blocks_until_all_quotes_verified(self):
        report = audit_packet_quotes(
            [
                "The clinician documented objective functional limitation and stated that the condition was aggravated during duty.",
                "The clinician conclusively established permanent causation.",
            ],
            self.sources,
        )
        self.assertEqual(report["quote_count"], 2)
        self.assertEqual(report["counts"]["verified"], 1)
        self.assertFalse(report["export_ready"])
        self.assertEqual(report["results"][1]["matches"], [])


if __name__ == "__main__":
    unittest.main()
