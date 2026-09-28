from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LAB = ROOT / "apps" / "forge-systems-lab"
for path in (str(SRC), str(LAB)):
    if path not in sys.path:
        sys.path.insert(0, path)

spec = importlib.util.spec_from_file_location("forge_systems_lessons_test", LAB / "lessons.py")
lessons = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lessons
assert spec.loader is not None
spec.loader.exec_module(lessons)


class ForgeSystemsLabTests(unittest.TestCase):
    def test_lessons_point_to_live_runtime_code(self):
        self.assertGreaterEqual(len(lessons.LESSONS), 23)
        for lesson in lessons.LESSONS:
            module = importlib.import_module(lesson["module"])
            self.assertTrue(
                hasattr(module, lesson["function"]),
                f'Missing {lesson["module"]}.{lesson["function"]}',
            )

    def test_pipeline_starts_with_policy_and_ends_with_renderer(self):
        self.assertEqual(lessons.PIPELINE[0], "Policy")
        self.assertIn("Asset Vault", lessons.PIPELINE)
        self.assertIn("Job Queue", lessons.PIPELINE)
        self.assertIn("FFmpeg Render", lessons.PIPELINE)
        self.assertIn("Local Memory", lessons.PIPELINE)
        self.assertIn("OCR", lessons.PIPELINE)
        self.assertIn("Model Catalog", lessons.PIPELINE)
        self.assertIn("Local Hybrid RAG", lessons.PIPELINE)
        self.assertIn("Direct Image Gen", lessons.PIPELINE)
        self.assertIn("Direct Video Gen", lessons.PIPELINE)
        self.assertIn("Local Kokoro Voice", lessons.PIPELINE)
        self.assertIn("Local Voice Fallback", lessons.PIPELINE)
        self.assertIn("Local Vision", lessons.PIPELINE)
        self.assertIn("Offline Pack", lessons.PIPELINE)
        self.assertEqual(lessons.PIPELINE[-1], "Final Local Render")


if __name__ == "__main__":
    unittest.main()
