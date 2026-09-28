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

    def test_episode_round_trip_from_dict(self):
        ep = engine.make_episode("Round Trip", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        restored = engine.episode_from_dict(ep.to_dict())
        self.assertEqual(restored.to_dict(), ep.to_dict())

    def test_source_locked_scene_framing_defaults_round_trip(self):
        ep = engine.make_episode("Source Lock", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        first = ep.scenes[0]
        self.assertEqual(first.focus_x, 50)
        self.assertEqual(first.focus_y, 50)
        self.assertEqual(first.source_zoom, 1.0)
        first.focus_x = 37
        first.focus_y = 62
        first.source_zoom = 1.45
        restored = engine.episode_from_dict(ep.to_dict())
        self.assertEqual(restored.scenes[0].focus_x, 37)
        self.assertEqual(restored.scenes[0].focus_y, 62)
        self.assertEqual(restored.scenes[0].source_zoom, 1.45)

    def test_legacy_episode_without_source_framing_still_loads(self):
        ep = engine.make_episode("Legacy", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        data = ep.to_dict()
        for scene in data["scenes"]:
            scene.pop("focus_x", None)
            scene.pop("focus_y", None)
            scene.pop("source_zoom", None)
        restored = engine.episode_from_dict(data)
        self.assertTrue(all(scene.focus_x == 50 for scene in restored.scenes))
        self.assertTrue(all(scene.focus_y == 50 for scene in restored.scenes))
        self.assertTrue(all(scene.source_zoom == 1.0 for scene in restored.scenes))

    def test_full_episode_manifest_has_multiple_shots(self):
        ep = engine.make_episode("Full Episode", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        manifest = engine.build_full_episode_manifest(
            ep,
            profile_name="Cinematic",
            video_engine="Wan 2.2",
            gpu_backend="Hugging Face ZeroGPU",
            tts_engine="Browser Speech",
            narrator_voice="Grim Chronicle",
        )
        self.assertEqual(manifest["production_mode"], "full_episode")
        self.assertEqual(manifest["shot_count"], len(ep.scenes) * 3)
        self.assertTrue(all(shot["status"] == "planned" for shot in manifest["shots"]))
        self.assertGreater(manifest["planned_generated_footage_seconds"], 0)

    def test_reference_library_note(self):
        # Reference URLs are project metadata only; render prompts must remain original.
        ep = engine.make_episode("Reference", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        manifest = engine.build_full_episode_manifest(
            ep,
            profile_name="Cinematic",
            video_engine="Wan 2.2",
            gpu_backend="Hugging Face ZeroGPU",
            tts_engine="Browser Speech",
            narrator_voice="Grim Chronicle",
            reference_url="https://youtu.be/example",
        )
        self.assertEqual(manifest["reference_url"], "https://youtu.be/example")
        self.assertTrue(all("do not reproduce" in shot["prompt"] for shot in manifest["shots"]))

    def test_benchmark_scorecard_is_transparent_planning_score(self):
        ep = engine.make_episode("Score", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        score = engine.benchmark_scorecard(ep, "Cinematic")
        self.assertGreater(score["overall"], 0)
        self.assertLessEqual(score["overall"], 100)
        self.assertTrue(any("not whether generated footage" in note for note in score["notes"]))

    def test_render_manifest_is_planned_and_portable(self):
        ep = engine.make_episode("Manifest", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        manifest = engine.build_render_manifest(
            ep,
            video_engine="CogVideoX-2B",
            gpu_backend="Kaggle T4x2",
            tts_engine="Browser Speech",
            narrator_voice="Grim Chronicle",
            reference_url="https://example.com/reference",
        )
        self.assertEqual(manifest["stage"], "planned")
        self.assertEqual(manifest["route_guidance"]["rating"], "preferred")
        self.assertEqual(len(manifest["scenes"]), len(ep.scenes))
        self.assertTrue(all(scene["status"] == "planned" for scene in manifest["scenes"]))

    def test_episode_is_deterministic_for_same_inputs(self):
        a = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        b = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_surprise_me_avoids_custom_placeholders(self):
        p = engine.random_presets("seed")
        self.assertTrue(all(value != "Custom" for value in p.values()))

    def test_gpu_backend_registry(self):
        self.assertEqual(next(iter(engine.GPU_BACKENDS)), "Local hardware (Creditless)")
        self.assertEqual(engine.GPU_BACKENDS["Local hardware (Creditless)"]["status"], "local")
        for name in ("Hugging Face ZeroGPU", "Kaggle T4x2", "Google Colab Free", "Lightning AI Free"):
            self.assertIn(name, engine.GPU_BACKENDS)
        self.assertIn("48 GB or 96 GB", engine.GPU_BACKENDS["Hugging Face ZeroGPU"]["hardware"])
        self.assertIn("T4", engine.GPU_BACKENDS["Kaggle T4x2"]["hardware"])

    def test_video_engine_registry(self):
        self.assertEqual(next(iter(engine.VIDEO_ENGINES)), "Deterministic Forge")
        self.assertEqual(engine.VIDEO_ENGINES["Deterministic Forge"]["status"], "connected")
        self.assertEqual(engine.VIDEO_ENGINES["Local Diffusers"]["status"], "adapter")
        for name in ("LTX-2", "Wan 2.2", "Mochi 1", "CogVideoX-2B"):
            self.assertIn(name, engine.VIDEO_ENGINES)
            self.assertEqual(engine.VIDEO_ENGINES[name]["status"], "planned")

    def test_tts_engine_registry(self):
        for name in ("Local Auto", "Kokoro", "KittenTTS", "MeloTTS", "Piper", "Browser Speech"):
            self.assertIn(name, engine.TTS_ENGINES)
        self.assertEqual(engine.TTS_ENGINES["Local Auto"]["status"], "connected")
        self.assertEqual(engine.TTS_ENGINES["Browser Speech"]["status"], "connected")
        self.assertEqual(engine.TTS_ENGINES["Kokoro"]["status"], "adapter")
        self.assertEqual(engine.TTS_ENGINES["Piper"]["status"], "adapter")

    def test_grim_chronicle_voice_profile(self):
        profile = engine.NARRATOR_VOICE_PROFILES["Grim Chronicle"]
        self.assertLess(profile["rate"], 1.0)
        self.assertLess(profile["pitch"], 1.0)
        self.assertIn("resonant", profile["description"].lower())
        self.assertTrue(profile["preferred_names"])

    def test_veyr_reports_local_fallback_for_final_episode(self):
        ep = engine.make_episode("A", self.presets, "Ashen Crown", "Enemy", "Commander", "Hold.")
        msg = engine.veyr_advice("What is missing for final episode", ep)
        self.assertIn("Deterministic Forge", msg)
        self.assertIn("local", msg.lower())


if __name__ == "__main__":
    unittest.main()
