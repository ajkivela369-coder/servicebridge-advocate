from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(APP))

from source_inventory import build_source_inventory


class SourceInventoryTests(unittest.TestCase):
    def test_inventory_reports_blank_and_missing_pages(self):
        sources = [
            {"source_name": "fictional_record.pdf", "page": 1, "text": "Page one text."},
            {"source_name": "fictional_record.pdf", "page": 2, "text": ""},
            {"source_name": "fictional_record.pdf", "page": 4, "text": "Page four text."},
        ]
        report = build_source_inventory(sources)
        self.assertEqual(report["document_count"], 1)
        doc = report["documents"][0]
        self.assertEqual(doc["page_range"], "1–2, 4")
        self.assertEqual(doc["blank_pages"], "2")
        self.assertEqual(doc["missing_pages"], "3")
        self.assertEqual(doc["status"], "review")

    def test_duplicate_filenames_remain_separate_documents(self):
        sources = [
            {"source_name": "duplicate.pdf", "page": 1, "text": "First fictional document."},
            {"source_name": "duplicate.pdf", "page": 2, "text": "Continuation."},
            {"source_name": "duplicate.pdf", "page": 1, "text": "Second fictional document."},
        ]
        report = build_source_inventory(sources)
        self.assertEqual(report["document_count"], 2)
        ids = {doc["source_id"] for doc in report["documents"]}
        self.assertEqual(len(ids), 2)


if __name__ == "__main__":
    unittest.main()
