import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "apps" / "medforge-imaging-studio" / "med_engine.py"
SPEC = importlib.util.spec_from_file_location("medforge_engine", MODULE_PATH)
engine = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = engine
assert SPEC.loader is not None
SPEC.loader.exec_module(engine)


class MedForgeEngineTests(unittest.TestCase):
    def test_mechanism_storyboard_separates_hypothesis_from_source(self):
        steps = engine.build_mechanism_steps(
            "cervical spine",
            "C1, C2 and adjacent soft tissue",
            "Dynamic / positional narrowing",
            "rotation and extension",
            "possible positional compression",
            "source.png",
        )
        self.assertEqual(len(steps), 6)
        self.assertEqual(steps[0].epistemic_status, "SOURCE-OBSERVED")
        self.assertTrue(any("HYPOTH" in step.epistemic_status for step in steps))
        self.assertEqual(steps[-1].epistemic_status, "EVIDENCE CHECK")

    def test_vlm_prompt_requires_uncertainty_and_no_diagnosis(self):
        prompt = engine.build_medical_vlm_prompt("MRI", "cervical spine", "What is visible?")
        self.assertIn("VISIBLE OBSERVATIONS", prompt)
        self.assertIn("UNCERTAINTY / LIMITATIONS", prompt)
        self.assertIn("Do not diagnose", prompt)
        self.assertIn("Do not infer causation", prompt)

    def test_render_manifest_has_source_fidelity_rules(self):
        label = engine.ImageLabel(
            id="L01",
            name="Example structure",
            lane="Source observation",
            note="Visible contour",
        )
        steps = engine.build_mechanism_steps(
            "region", "structure", "Compression", "motion", "possible effect"
        )
        manifest = engine.build_render_manifest("Study", "source.png", [label], steps)
        self.assertEqual(manifest["stage"], "planned")
        self.assertTrue(manifest["render_rules"]["preserve_source_pixels"])
        self.assertTrue(manifest["render_rules"]["source_and_reconstruction_visually_distinct"])
        self.assertTrue(manifest["render_rules"]["do_not_present_hypothesis_as_observation"])

    def test_label_round_trip(self):
        label = engine.ImageLabel(
            id="L01",
            name="C1",
            lane="Measurement",
            note="Example",
            x=31,
            y=44,
            confidence="Measured",
            source_ref="p. 2",
        )
        restored = engine.label_from_dict(label.to_dict())
        self.assertEqual(restored.to_dict(), label.to_dict())


if __name__ == "__main__":
    unittest.main()
