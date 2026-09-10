from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDITOR_DIR = ROOT / "portfolio" / "evidence-auditor"
sys.path.insert(0, str(AUDITOR_DIR))

from auditor import audit_sources
from elias_memory import default_memory, export_memory, import_memory, memory_context, summarize_workspace
from elias_plugins import default_plugin_state, respond


class EliasMemoryPluginTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "source_name": "clinic_note.pdf",
                "page": 2,
                "text": "The clinician documented objective functional limitation and stated that work tolerance was reduced.",
            },
            {
                "source_name": "review.pdf",
                "page": 4,
                "text": "The administrative review stated that additional records were unavailable and the record may be incomplete.",
            },
        ]
        self.result = audit_sources(self.sources)

    def test_memory_round_trip_is_explicit_and_small(self):
        memory = default_memory()
        memory["case_label"] = "Synthetic VA case"
        memory["goal"] = "Prepare a source-grounded packet"
        memory["auto_summary"] = summarize_workspace(self.result, self.sources)
        exported = export_memory(memory)
        restored = import_memory(exported)
        self.assertEqual(restored["case_label"], "Synthetic VA case")
        self.assertIn("Loaded record", restored["auto_summary"])
        self.assertIn("Prepare a source-grounded packet", memory_context(restored))

    def test_memory_can_be_disabled(self):
        memory = default_memory()
        memory["enabled"] = False
        memory["notes"] = "Should not be surfaced"
        self.assertEqual(memory_context(memory), "")

    def test_plugin_router_reports_tools_used(self):
        response = respond(
            "What is the strongest evidence in this record?",
            self.result,
            self.sources,
            plugins=default_plugin_state(),
            memory_context="Case: synthetic",
        )
        self.assertIn("Record Search", response["tools_used"])
        self.assertTrue(response["grounded"])

    def test_memory_question_uses_memory_not_unrelated_evidence(self):
        response = respond(
            "What do you remember about this case?",
            self.result,
            self.sources,
            plugins=default_plugin_state(),
            memory_context="Case: Synthetic VA case | Goal: source-grounded review",
        )
        self.assertEqual(response["mode"], "memory")
        self.assertIn("Synthetic VA case", response["answer"])
        self.assertEqual(response["citations"], [])


if __name__ == "__main__":
    unittest.main()
