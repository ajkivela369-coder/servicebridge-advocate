from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(APP))

from auditor import audit_sources
from packet_assurance import assess_packet_assurance
from packet_builder import build_packet


class PacketReconciliationPdfTests(unittest.TestCase):
    def _pdf_text(self, pdf_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(pdf_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    def test_assurance_pdf_surfaces_source_reconciliation_cues(self):
        sources = [
            {
                "source_name": "fictional_record.pdf",
                "page": 1,
                "text": "The clinician documented objective functional limitation during duty.",
            },
            {
                "source_name": "fictional_record.pdf",
                "page": 2,
                "text": "",
            },
            {
                "source_name": "fictional_record.pdf",
                "page": 4,
                "text": "A follow-up note documented continued functional limitation.",
            },
        ]
        result = audit_sources(sources)
        assurance = assess_packet_assurance(result["items"], sources, [])
        pdf = build_packet(
            result,
            packet_style="formal_review",
            case_title="Fictional Reconciliation Test",
            assurance=assurance,
        )
        text = self._pdf_text(pdf)
        self.assertIn("Source Reconciliation", text)
        self.assertIn("fictional_record.pdf", text)
        self.assertIn("SRC-", text)
        self.assertIn("Blank: 2", text)
        self.assertIn("Missing: 3", text)
        self.assertIn("not proof that an original document is incomplete", text)

    def test_packet_still_builds_without_assurance_inventory(self):
        sources = [{
            "source_name": "fictional_record.pdf",
            "page": 1,
            "text": "The clinician documented objective functional limitation during duty.",
        }]
        result = audit_sources(sources)
        pdf = build_packet(
            result,
            packet_style="visual_claim",
            case_title="Compatibility Test",
            assurance=None,
        )
        self.assertGreater(len(pdf), 1000)


if __name__ == "__main__":
    unittest.main()
