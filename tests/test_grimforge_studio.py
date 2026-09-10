from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "portfolio" / "grimforge-studio"
sys.path.insert(0, str(APP_DIR))

from engine import (
    REFERENCE_DNA,
    blend_reference_dna,
    build_director_timeline,
    build_script_blueprint,
    rights_gate,
)


class GrimForgeStudioTests(unittest.TestCase):
    def test_reference_blend_stays_in_range(self):
        weights = {name: 1 for name in REFERENCE_DNA}
        blend = blend_reference_dna(weights)
        self.assertEqual(set(blend), {"narrator", "humor", "cinematic", "depth", "motion", "pace"})
        self.assertTrue(all(0 <= value <= 100 for value in blend.values()))

    def test_director_timeline_is_ordered_and_labels_interpretation(self):
        scenes = build_director_timeline(
            "Synthetic empire",
            "why its victories reproduce its crises",
            "Grimdark Galaxy",
            18,
            40,
            85,
            90,
        )
        self.assertEqual(len(scenes), 8)
        self.assertEqual(scenes[0].start, "00:00")
        self.assertTrue(any(scene.canon_label == "INTERPRETATION" for scene in scenes))
        self.assertTrue(all(scene.duration_seconds > 0 for scene in scenes))

    def test_script_blueprint_requires_counterweight(self):
        blueprint = build_script_blueprint("Synthetic subject", "Synthetic thesis", "Grimdark Galaxy", 90, 40)
        names = [row["section"] for row in blueprint]
        self.assertIn("Counterweight", names)
        self.assertIn("Evidence Ladder", names)

    def test_rights_gate_blocks_reference_only_assets(self):
        result = rights_gate([
            {"name": "original", "rights": "Original AI artwork"},
            {"name": "reference", "rights": "Third-party / reference only"},
        ])
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["blocked"]), 1)


if __name__ == "__main__":
    unittest.main()
