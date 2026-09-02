import tempfile
import unittest
from pathlib import Path

from servicebridge.advocate import Advocate
from servicebridge.ingest import ingest_file
from servicebridge.models import AdvocacyMode, AdvocacyRequest, BenefitLane, EvidenceClass
from servicebridge.store import EvidenceStore


class AdvocateTests(unittest.TestCase):
    def test_prompt_contains_lane_and_cited_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = root / "orders.txt"
            record.write_text("Orders identify a period of full-time training in October 2021.")
            source, chunks = ingest_file(record, EvidenceClass.OFFICIAL_RECORD)
            with EvidenceStore(root / "case.sqlite3") as store:
                store.add_document(source, chunks)
                response = Advocate(store).answer(
                    AdvocacyRequest(
                        question="What do the training orders establish?",
                        lane=BenefitLane.VA_SERVICE_CONNECTION,
                        mode=AdvocacyMode.PRIVATE_ANALYSIS,
                    )
                )
            self.assertIn("For Guard/Reserve service", response.answer)
            self.assertIn(source.source_id, response.answer)
            self.assertEqual(response.retrieved_chunks, 1)


if __name__ == "__main__":
    unittest.main()
