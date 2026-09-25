import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("pipeline.py")
SPEC = importlib.util.spec_from_file_location("evidence_pipe_pipeline", MODULE_PATH)
pipeline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pipeline)


class EvidencePipeTests(unittest.TestCase):
    def test_date_normalization(self):
        self.assertEqual(pipeline.normalize_date("09/01/2026"), "2026-09-01")
        self.assertEqual(pipeline.normalize_date("September 1, 2026"), "2026-09-01")

    def test_duplicate_fingerprint_ignores_whitespace_and_case(self):
        a = {
            "source_type": "clinical_record",
            "title": "Example",
            "date": "2026-09-01",
            "text": "Finding one.",
        }
        b = {
            "source_type": "CLINICAL_RECORD",
            "title": "EXAMPLE",
            "date": "2026-09-01",
            "text": "  Finding   one. ",
        }
        self.assertEqual(pipeline.stable_fingerprint(a), pipeline.stable_fingerprint(b))

    def test_missing_required_field_is_rejected(self):
        with self.assertRaises(ValueError):
            pipeline.transform(
                {
                    "record_id": "SYN-X",
                    "source_type": "clinical_record",
                    "title": "Missing text",
                    "date": "2026-09-01",
                }
            )


if __name__ == "__main__":
    unittest.main()
