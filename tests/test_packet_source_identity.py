from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import sys
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from auditor import audit_sources
from packet_assurance import assess_packet_assurance
from packet_builder import build_packet


class PacketSourceIdentityTests(unittest.TestCase):
    @staticmethod
    def pdf_text(payload: bytes) -> str:
        reader = PdfReader(BytesIO(payload))
        raw = "\n".join((page.extract_text() or "") for page in reader.pages)
        return " ".join(raw.split())

    def test_exported_packet_shows_source_id_in_evidence_and_appendix(self):
        sources = [
            {
                "source_name": "fictional_exam.pdf",
                "page": 1,
                "text": "The clinician documented objective functional limitation during duty.",
            }
        ]
        result = audit_sources(sources)
        source_id = result["items"][0]["source_id"]
        self.assertRegex(source_id, r"^SRC-[A-F0-9]{10}$")

        text = self.pdf_text(build_packet(result, case_title="Fictional Provenance Review"))
        self.assertIn(source_id, text)
        self.assertIn("Source ID", text)
        self.assertIn("Stable source IDs distinguish document instances", text)

    def test_duplicate_filenames_remain_distinguishable_in_source_appendix(self):
        sources = [
            {"source_name": "duplicate.pdf", "page": 1, "text": "Objective finding was documented."},
            {"source_name": "duplicate.pdf", "page": 2, "text": "Functional limitation continued."},
            {"source_name": "duplicate.pdf", "page": 1, "text": "A separate review stated no evidence was found."},
        ]
        result = audit_sources(sources)
        source_ids = result["source_ids"]
        self.assertEqual(len(source_ids), 2)

        text = self.pdf_text(build_packet(result))
        for source_id in source_ids:
            self.assertIn(source_id, text)

    def test_quote_verification_register_includes_verified_source_id(self):
        sources = [
            {
                "source_name": "fictional_quote_source.pdf",
                "page": 3,
                "text": "The witness reported continuity of symptoms after training.",
            }
        ]
        result = audit_sources(sources)
        assurance = assess_packet_assurance(
            result["items"],
            sources,
            ["The witness reported continuity of symptoms after training."],
        )
        source_id = assurance["quotes"]["results"][0]["matches"][0]["source_id"]

        text = self.pdf_text(build_packet(result, assurance=assurance))
        self.assertIn("Quote Verification Register", text)
        self.assertIn(source_id, text)


if __name__ == "__main__":
    unittest.main()
