from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from auditor import audit_sources, verify_quote
from source_identity import assign_source_ids


class SourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {"source_name": "synthetic_record.pdf", "page": 1, "text": "Fictional first document page one."},
            {"source_name": "synthetic_record.pdf", "page": 2, "text": "Fictional first document page two."},
            {"source_name": "synthetic_record.pdf", "page": 1, "text": "Fictional second document with the same filename."},
        ]

    def test_page_reset_distinguishes_duplicate_filenames(self):
        identified = assign_source_ids(self.sources)
        self.assertEqual(identified[0]["source_id"], identified[1]["source_id"])
        self.assertNotEqual(identified[1]["source_id"], identified[2]["source_id"])

    def test_source_ids_are_short_noncontent_fingerprints(self):
        identified = assign_source_ids(self.sources)
        for source in identified:
            source_id = source["source_id"]
            self.assertRegex(source_id, r"^SRC-[0-9A-F]{10}$")
            self.assertNotIn("synthetic", source_id.lower())
            self.assertNotIn("fictional", source_id.lower())

    def test_audit_and_quote_results_preserve_source_identity(self):
        result = audit_sources(self.sources)
        ids = {item["source_id"] for item in result["items"]}
        self.assertEqual(len(ids), 2)
        self.assertEqual(set(result["source_ids"]), ids)

        verification = verify_quote("Fictional second document with the same filename.", self.sources)
        self.assertEqual(verification["status"], "verified")
        self.assertTrue(re.fullmatch(r"SRC-[0-9A-F]{10}", verification["matches"][0]["source_id"]))

    def test_explicit_source_id_is_preserved_for_compatibility(self):
        identified = assign_source_ids([
            {"source_name": "synthetic.pdf", "page": 1, "text": "Public-safe text.", "source_id": "SRC-EXTERNAL01"}
        ])
        self.assertEqual(identified[0]["source_id"], "SRC-EXTERNAL01")


if __name__ == "__main__":
    unittest.main()
