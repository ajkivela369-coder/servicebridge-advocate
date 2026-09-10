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
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

auditor = load_module("evidence_auditor_auditor", AUDITOR_DIR / "auditor.py")
packet_builder = load_module("evidence_auditor_packet_builder", AUDITOR_DIR / "packet_builder.py")

class EvidenceAuditorV2Tests(unittest.TestCase):
    def test_page_provenance_and_quote_verification(self):
        sources=[{"source_name":"synthetic_exam.pdf","page":3,"text":"The clinician documented objective functional limitation during duty."}]
        result=auditor.audit_sources(sources)
        self.assertEqual(result["items"][0]["source_name"],"synthetic_exam.pdf")
        self.assertEqual(result["items"][0]["page"],3)
        verification=auditor.verify_quote("The clinician documented objective functional limitation during duty.",sources)
        self.assertEqual(verification["status"],"verified")
        self.assertEqual(verification["matches"][0]["page"],3)

    def test_dual_packet_styles_generate_pdf(self):
        result=auditor.audit_text("The clinician documented objective functional limitation. A later review stated there was no evidence linking the symptoms to service.")
        for style in ("visual_claim","formal_review"):
            payload=packet_builder.build_packet(result,packet_style=style,mechanism_steps=["Event","Finding","Functional impact"])
            self.assertTrue(payload.startswith(b"%PDF"))
            self.assertGreater(len(payload),1000)

if __name__=="__main__":
    unittest.main()
