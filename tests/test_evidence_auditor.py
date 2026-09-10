from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

auditor = load_module("evidence_auditor_auditor", AUDITOR_DIR / "auditor.py")
packet_builder = load_module("evidence_auditor_packet_builder", AUDITOR_DIR / "packet_builder.py")
readiness = load_module("evidence_auditor_readiness", AUDITOR_DIR / "readiness.py")
quote_integrity = load_module("evidence_auditor_quote_integrity", AUDITOR_DIR / "quote_integrity.py")

class EvidenceAuditorV2Tests(unittest.TestCase):
    def test_page_provenance_and_quote_verification(self):
        sources=[{"source_name":"synthetic_exam.pdf","page":3,"text":"The clinician documented objective functional limitation during duty."}]
        result=auditor.audit_sources(sources)
        self.assertEqual(result["items"][0]["source_name"],"synthetic_exam.pdf")
        self.assertEqual(result["items"][0]["page"],3)
        verification=auditor.verify_quote("The clinician documented objective functional limitation during duty.",sources)
        self.assertEqual(verification["status"],"verified")
        self.assertEqual(verification["matches"][0]["page"],3)

    def test_contextual_quote_verification_returns_neighboring_context(self):
        sources=[{
            "source_name":"synthetic_exam.pdf",
            "page":3,
            "text":"History was reviewed. The clinician documented objective functional limitation during duty. Follow-up was recommended."
        }]
        result=quote_integrity.verify_quote_contextual(
            "The clinician documented objective functional limitation during duty.",
            sources,
        )
        self.assertEqual(result["status"],"verified")
        self.assertEqual(result["confidence"],1.0)
        self.assertIn("History was reviewed",result["matches"][0]["context"]["before"])
        self.assertIn("Follow-up was recommended",result["matches"][0]["context"]["after"])

    def test_contextual_quote_verification_never_labels_fuzzy_match_exact(self):
        sources=[{
            "source_name":"synthetic_exam.pdf",
            "page":4,
            "text":"The examiner documented persistent functional limitations after training."
        }]
        result=quote_integrity.verify_quote_contextual(
            "The examiner documented persistent functional limitation after training.",
            sources,
        )
        self.assertEqual(result["status"],"partial")
        self.assertLess(result["confidence"],1.0)
        self.assertEqual(result["matches"][0]["match_type"],"similar_not_exact")

    def test_contextual_quote_verification_rejects_unrelated_text(self):
        sources=[{"source_name":"synthetic_notice.pdf","page":1,"text":"The administrative notice scheduled a routine review."}]
        result=quote_integrity.verify_quote_contextual(
            "The physician concluded the condition was caused by training.",
            sources,
        )
        self.assertEqual(result["status"],"not_found")

    def test_dual_packet_styles_generate_pdf(self):
        result=auditor.audit_text("The clinician documented objective functional limitation. A later review stated there was no evidence linking the symptoms to service.")
        for style in ("visual_claim","formal_review"):
            payload=packet_builder.build_packet(result,packet_style=style,mechanism_steps=["Event","Finding","Functional impact"])
            self.assertTrue(payload.startswith(b"%PDF"))
            self.assertGreater(len(payload),1000)

    def test_provenance_readiness_rewards_locatable_sources(self):
        complete=[
            {"source_name":"synthetic_exam.pdf","page":1,"text":"Finding one."},
            {"source_name":"synthetic_exam.pdf","page":2,"text":"Finding two."},
        ]
        incomplete=[
            {"source_name":"synthetic_exam.pdf","page":None,"text":"Finding one."},
            {"source_name":"Unknown source","page":None,"text":""},
        ]
        complete_score=readiness.assess_provenance_readiness(complete)
        incomplete_score=readiness.assess_provenance_readiness(incomplete)
        self.assertEqual(complete_score["score"],100)
        self.assertGreater(complete_score["score"],incomplete_score["score"])
        self.assertIn("page locator", " ".join(incomplete_score["flags"]).lower())

if __name__=="__main__":
    unittest.main()
