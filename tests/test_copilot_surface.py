from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"


class EliasSurfaceTests(unittest.TestCase):
    def test_public_navigation_is_three_destinations(self):
        page_names = sorted(path.name for path in (AUDITOR_DIR / "pages").glob("*.py"))
        self.assertEqual(page_names, ["2_Case_Review.py", "3_Packet_Studio.py"])
        shell = (AUDITOR_DIR / "ui_shell.py").read_text(encoding="utf-8")
        self.assertIn('label="Elias"', shell)
        self.assertIn('label="Case Review"', shell)
        self.assertIn('label="Packet Studio"', shell)

    def test_elias_is_the_main_chat_workspace(self):
        dashboard = (AUDITOR_DIR / "dashboard.py").read_text(encoding="utf-8")
        self.assertIn('st.chat_input("Message Elias")', dashboard)
        self.assertIn("elias_threads", dashboard)
        self.assertIn("Tools / plugins", dashboard)
        self.assertIn("Memory", dashboard)
        self.assertIn("Case files", dashboard)
        self.assertNotIn("assistant_bot", dashboard)

    def test_reviewer_pages_mount_ask_elias(self):
        for filename in ["2_Case_Review.py", "3_Packet_Studio.py"]:
            source = (AUDITOR_DIR / "pages" / filename).read_text(encoding="utf-8")
            with self.subTest(page=filename):
                self.assertIn("render_page_copilot", source)

        floating = (AUDITOR_DIR / "floating_assistant.py").read_text(encoding="utf-8")
        self.assertIn("ea-elias-fab", floating)
        self.assertIn("Ask Elias", floating)
        self.assertNotIn("Open full Copilot workspace", floating)

    def test_obsolete_assistant_surfaces_stay_removed(self):
        self.assertFalse((AUDITOR_DIR / "assistant_bot.py").exists())
        self.assertFalse((AUDITOR_DIR / "pages" / "8_Evidence_Copilot.py").exists())
        self.assertFalse((AUDITOR_DIR / "pages" / "1_Elias_Assistant.py").exists())
        self.assertTrue((AUDITOR_DIR / "copilot_engine.py").exists())


if __name__ == "__main__":
    unittest.main()
