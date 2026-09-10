from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"


class CopilotSurfaceTests(unittest.TestCase):
    def test_obsolete_assistant_bot_entrypoint_stays_removed(self):
        self.assertFalse((AUDITOR_DIR / "assistant_bot.py").exists())
        self.assertTrue((AUDITOR_DIR / "copilot_engine.py").exists())
        self.assertTrue((AUDITOR_DIR / "pages" / "8_Evidence_Copilot.py").exists())

    def test_reviewer_pages_mount_persistent_copilot(self):
        reviewer_pages = [
            "2_Review_Readiness.py",
            "3_Quote_Integrity.py",
            "4_Packet_Integrity.py",
            "5_Coverage_Gaps.py",
            "7_Packet_Assurance.py",
        ]
        for filename in reviewer_pages:
            source = (AUDITOR_DIR / "pages" / filename).read_text(encoding="utf-8")
            with self.subTest(page=filename):
                self.assertIn("render_page_copilot", source)

    def test_elias_remains_a_separate_workspace(self):
        elias = (AUDITOR_DIR / "pages" / "6_Elias_Assistant.py").read_text(encoding="utf-8")
        self.assertNotIn("render_page_copilot", elias)
        self.assertIn("Elias", elias)


if __name__ == "__main__":
    unittest.main()
