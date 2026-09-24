import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "apps" / "grimforge-war-theater" / "war_engine.py"
SPEC = importlib.util.spec_from_file_location("grimforge_war_engine", MODULE_PATH)
engine = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = engine
assert SPEC.loader is not None
SPEC.loader.exec_module(engine)


class GrimForgeWarEngineTests(unittest.TestCase):
    def setUp(self):
        self.presets = {group: options[0] for group, options in engine.PRESETS.items()}

    def test_episode_has_requested_scene_count_and_runtime(self):
        ep = engine.make_episode(
            "Test Siege", self.presets, "Ashen Crown", "Enemy", "Commander",
            "Hold the bridge.", custom_minutes=12, scene_count=9
        )
        self.assertEqual(len(ep.scenes), 9)
        self.assertEqual(sum(scene.duration for scene in ep.scenes), ep.runtime_seconds)

    def test_episode_is_deterministic_for_same_inputs(self):
        a = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        b = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_surprise_me_avoids_custom_placeholders(self):
        p = engine.random_presets("seed")
        self.assertTrue(all(value != "Custom" for value in p.values()))

    def test_gpu_backend_registry(self):
        expected = ("Hugging Face ZeroGPU", "Kaggle T4x2", "Google Colab Free", "Lightning AI Free")
        self.assertEqual(tuple(engine.GPU_BACKENDS.keys()), expected)
        self.assertIn("48 GB or 96 GB", engine.GPU_BACKENDS["Hugging Face ZeroGPU"]["hardware"])
        self.assertIn("T4", engine.GPU_BACKENDS["Kaggle T4x2"]["hardware"])

    def test_video_engine_registry(self):
        expected = ("LTX-2", "Wan 2.2", "Mochi 1", "CogVideoX-2B")
        self.assertEqual(tuple(engine.VIDEO_ENGINES.keys()), expected)
        self.assertTrue(all(engine.VIDEO_ENGINES[name]["status"] == "planned" for name in expected))

    def test_tts_engine_registry(self):
        for name in ("Kokoro", "KittenTTS", "MeloTTS", "Piper", "Browser Speech"):
            self.assertIn(name, engine.TTS_ENGINES)
        self.assertEqual(engine.TTS_ENGINES["Browser Speech"]["status"], "connected")
        self.assertEqual(engine.TTS_ENGINES["Kokoro"]["status"], "planned")

    def test_grim_chronicle_voice_profile(self):
        profile = engine.NARRATOR_VOICE_PROFILES["Grim Chronicle"]
        self.assertLess(profile["rate"], 1.0)
        self.assertLess(profile["pitch"], 1.0)
        self.assertIn("resonant", profile["description"].lower())
        self.assertTrue(profile["preferred_names"])

    def test_veyr_reports_missing_provider_for_final_episode(self):
        ep = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        msg = engine.veyr_advice("What is missing for final episode", ep)
        self.assertIn("full-motion MP4", msg)


if __name__ == "__main__":
    unittest.main()
