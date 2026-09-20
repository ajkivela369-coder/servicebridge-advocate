from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "portfolio" / "evidence-auditor" / "00_CURRENT_APP" / "reference" / "filing_policy.py"


def load_policy():
    spec = importlib.util.spec_from_file_location("elias_v8_filing_policy", POLICY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


policy = load_policy()


class EliasV8FilingPolicyTests(unittest.TestCase):
    def test_va_missing_lod_is_development_gap_without_actual_adverse_finding(self):
        result = policy.missing_record_interpretation("line-of-duty determination")
        self.assertIn("development gap", result)
        self.assertIn("not affirmative negative evidence", result)

    def test_ssa_architecture_is_rfc_and_five_step_specific(self):
        sections = policy.agency_sections("Social Security (SSDI / SSI)")
        self.assertIn("five_step_framework", sections)
        self.assertIn("rfc_by_function", sections)
        self.assertIn("sustained_work_reliability", sections)
        self.assertNotIn("duty_status_chronology", sections)

    def test_preflight_blocks_empty_authority_and_missing_issue_argument(self):
        result = policy.submission_preflight({
            "legal_authorities": [],
            "issues": ["Synthetic lumbar limitation", "Synthetic shoulder limitation"],
            "arguments": [
                {
                    "issue": "Synthetic lumbar limitation",
                    "source_citations": ["SRC-EXAMPLE-001"],
                    "requires_pinpoint": True,
                    "has_pinpoint": True,
                }
            ],
            "source_appendix": [],
            "literature": [],
        })
        self.assertEqual(result.status, "Draft")
        self.assertTrue(any("authorities" in item.lower() for item in result.blockers))
        self.assertTrue(any("shoulder" in item.lower() for item in result.blockers))

    def test_source_appendix_is_deduplicated_and_limited_to_cited_sources(self):
        sources = [
            {"source_id": "SRC-EXAMPLE-001", "name": "synthetic_exam.pdf"},
            {"source_id": "SRC-EXAMPLE-001", "name": "synthetic_exam_duplicate.pdf"},
            {"source_id": "SRC-EXAMPLE-002", "name": "synthetic_notice.pdf"},
            {"source_id": "SRC-EXAMPLE-003", "name": "synthetic_uncited.pdf"},
        ]
        output = policy.dedupe_cited_sources(
            sources,
            ["SRC-EXAMPLE-001", "SRC-EXAMPLE-002"],
        )
        self.assertEqual([item["source_id"] for item in output], ["SRC-EXAMPLE-001", "SRC-EXAMPLE-002"])

    def test_similar_wording_is_never_promoted_to_exact_quote(self):
        source = "The clinician documented persistent functional limitations after training."
        proposed = "The clinician documented persistent functional limitation after training."
        self.assertEqual(policy.classify_quote(proposed, source), "paraphrase")
        self.assertEqual(policy.classify_quote(source, source), "exact_quote")

    def test_clean_synthetic_packet_can_reach_ready_to_submit(self):
        result = policy.submission_preflight({
            "legal_authorities": [{"label": "Synthetic governing rule"}],
            "issues": ["Synthetic functional limitation"],
            "arguments": [{
                "issue": "Synthetic functional limitation",
                "source_citations": ["SRC-EXAMPLE-001"],
                "requires_pinpoint": True,
                "has_pinpoint": True,
            }],
            "source_appendix": [{
                "source_id": "SRC-EXAMPLE-001",
                "name": "synthetic_exam.pdf",
                "cited": True,
            }],
            "literature": [{"title": "Synthetic review article", "relevance_score": 0.91}],
        })
        self.assertEqual(result.status, "Ready to Submit")
        self.assertFalse(result.blockers)
        self.assertFalse(result.warnings)


if __name__ == "__main__":
    unittest.main()
