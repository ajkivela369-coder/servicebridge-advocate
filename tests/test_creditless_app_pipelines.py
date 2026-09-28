from __future__ import annotations

import base64
from io import BytesIO
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GRIM = ROOT / "apps" / "grimforge-war-theater"
WILD = ROOT / "apps" / "wildtake-streamlit"
MED = ROOT / "apps" / "medforge-imaging-studio"
for path in (str(GRIM), str(WILD), str(MED)):
    if path not in sys.path:
        sys.path.insert(0, path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


grim = load("grim_local_pipeline_test", GRIM / "local_pipeline.py")
wild = load("wild_local_pipeline_test", WILD / "local_pipeline.py")
native3d = load("med_native3d_pipeline_test", MED / "med_native3d.py")
motion_mod = load("med_motion_pipeline_test", MED / "med_motion.py")

from servicebridge.local_runtime import RuntimeMode, RuntimePolicy
from servicebridge.local_runtime.vision import LocalVisionClient, build_vision_payload


class GrimForgeLocalPipelineTests(unittest.TestCase):
    def test_scene_cards_and_fast_timing_need_no_tts(self):
        episode = {
            "title": "Test",
            "scenes": [
                {
                    "id": "S01",
                    "act": "Act I",
                    "title": "Opening",
                    "duration": 90,
                    "visual": "A bridge at dusk.",
                    "narration": "The army arrives.",
                    "dialogue": "",
                },
                {
                    "id": "S02",
                    "act": "Act I",
                    "title": "Contact",
                    "duration": 50,
                    "visual": "The first clash.",
                    "narration": "Steel meets steel.",
                    "dialogue": "Hold.",
                },
            ],
        }
        image = Image.new("RGB", (64, 64), "black")
        buf = BytesIO()
        image.save(buf, format="PNG")
        data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

        with tempfile.TemporaryDirectory() as directory:
            prepared = grim.prepare_grimforge_local_assets(
                episode,
                output_dir=directory,
                source_media={"data_uri": data_uri},
                use_local_tts=False,
                scene_duration_cap=12,
            )
            self.assertEqual(len(prepared["scenes"]), 2)
            self.assertEqual(prepared["scenes"][0].duration, 12)
            self.assertEqual(prepared["scenes"][1].duration, 12)
            self.assertTrue(prepared["source_locked_image_used"])
            self.assertTrue(Path(prepared["captions_path"]).is_file())
            self.assertTrue(Path(prepared["scenes"][0].image_path).is_file())


class WildTakeLocalPipelineTests(unittest.TestCase):
    def test_timestamp_and_cues(self):
        beats = [
            wild.WildTakeBeat("00:02", "First"),
            wild.WildTakeBeat("00:05", "Second"),
        ]
        cues = wild.beats_to_cues(beats, 8.0)
        self.assertEqual(wild.parse_timestamp("1:02.5"), 62.5)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start, 2.0)
        self.assertEqual(cues[0].end, 5.0)
        self.assertEqual(cues[1].end, 8.0)


class LocalVisionTests(unittest.TestCase):
    def test_vision_payload_contains_local_image_and_question(self):
        payload = build_vision_payload(
            model="vlm",
            image_data_uri="data:image/png;base64,AAAA",
            instructions="Separate observations.",
            question="What is visible?",
        )
        self.assertEqual(payload["model"], "vlm")
        content = payload["messages"][1]["content"]
        self.assertEqual(content[0]["text"], "What is visible?")
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/png"))

    def test_creditless_vision_blocks_external_endpoint(self):
        with self.assertRaises(PermissionError):
            LocalVisionClient(
                endpoint="https://api.example.com/v1/chat/completions",
                policy=RuntimePolicy(mode=RuntimeMode.CREDITLESS),
            )


class Native3DTransformTests(unittest.TestCase):
    def test_motion_interpolates_and_preserves_center_rotation(self):
        vertices = __import__("numpy").array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ])
        motion = motion_mod.build_motion(
            "structure",
            translation_mm_xyz=(10, 0, 0),
            rotation_deg_xyz=(0, 0, 180),
            start_frame=1,
            end_frame=11,
        )
        self.assertAlmostEqual(native3d.motion_fraction(motion, 6), 0.5)
        transformed = native3d.transform_vertices(vertices, motion, 11)
        # 180-degree rotation around center swaps the two x positions, then +10 mm.
        self.assertAlmostEqual(transformed[0, 0], 12.0, places=5)
        self.assertAlmostEqual(transformed[1, 0], 10.0, places=5)


if __name__ == "__main__":
    unittest.main()
