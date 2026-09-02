import tempfile
import unittest
from pathlib import Path

from servicebridge.ingest import ingest_file
from servicebridge.models import EvidenceClass
from servicebridge.store import EvidenceStore


class StoreTests(unittest.TestCase):
    def test_ingest_and_search_preserve_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "note.txt"
            source_path.write_text("Documented migraine symptoms affected attendance and pace.")
            source, chunks = ingest_file(source_path, EvidenceClass.CLINICAL_RECORD)
            with EvidenceStore(root / "case.sqlite3") as store:
                store.add_document(source, chunks)
                hits = store.search("migraine attendance")
            self.assertTrue(hits)
            self.assertEqual(hits[0].chunk.source_id, source.source_id)
            self.assertEqual(hits[0].chunk.evidence_class, EvidenceClass.CLINICAL_RECORD)


if __name__ == "__main__":
    unittest.main()
