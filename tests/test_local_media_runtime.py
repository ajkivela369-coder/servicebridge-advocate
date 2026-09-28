from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from servicebridge.local_runtime.audio import mix_voice_music_command
from servicebridge.local_runtime.captions import (
    CaptionCue,
    cues_to_srt,
    scene_narration_to_cues,
    seconds_to_srt_time,
)
from servicebridge.local_runtime.render import (
    LocalRenderPlan,
    LocalSceneAsset,
    build_render_commands,
)
from servicebridge.local_runtime.workflows import (
    LocalWorkflow,
    LocalWorkflowCatalog,
    substitute_variables,
)


class LocalCaptionTests(unittest.TestCase):
    def test_srt_time_and_scene_cues(self):
        self.assertEqual(seconds_to_srt_time(61.234), "00:01:01,234")
        cues = scene_narration_to_cues(
            [
                {"duration": 3, "narration": "First scene narration."},
                {"duration": 2, "narration": "Second scene narration."},
            ]
        )
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[1].start, 3)
        text = cues_to_srt(cues)
        self.assertIn("00:00:03,000 --> 00:00:05,000", text)

    def test_empty_captions_are_skipped(self):
        text = cues_to_srt([CaptionCue(0, 1, " "), CaptionCue(1, 2, "Visible")])
        self.assertIn("Visible", text)
        self.assertNotIn("\n1\n00:00:00,000", text)


class LocalWorkflowTests(unittest.TestCase):
    def test_recursive_workflow_variables(self):
        value = {
            "prompt": "{{prompt}}",
            "nested": [{"seed": "{{seed}}"}],
        }
        out = substitute_variables(value, {"prompt": "castle", "seed": 42})
        self.assertEqual(out["prompt"], "castle")
        self.assertEqual(out["nested"][0]["seed"], "42")

    def test_catalog_loads_only_registered_local_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow_file = root / "workflow.json"
            workflow_file.write_text(json.dumps({"node": {"text": "{{prompt}}"}}))
            catalog = LocalWorkflowCatalog(root / "catalog.json")
            catalog.add(
                LocalWorkflow(
                    workflow_id="image-basic",
                    kind="image",
                    path=str(workflow_file),
                )
            )
            loaded = catalog.load("image-basic", {"prompt": "red panda"})
            self.assertEqual(loaded["node"]["text"], "red panda")
            self.assertTrue(catalog.verify("image-basic")["valid_json"])


class LocalAudioTests(unittest.TestCase):
    def test_voice_music_mix_uses_local_ffmpeg_and_ducking(self):
        cmd = mix_voice_music_command("voice.wav", "music.wav", "mix.m4a", duration=10)
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertTrue(any("sidechaincompress" in part for part in cmd))
        self.assertIn("10.000", cmd)


class LocalRenderRunnerTests(unittest.TestCase):
    def test_render_plan_builds_segments_concat_and_subtitles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            img1 = root / "one.png"
            img2 = root / "two.png"
            audio = root / "voice.wav"
            captions = root / "captions.srt"
            for path in (img1, img2, audio, captions):
                path.write_bytes(b"x")

            plan = LocalRenderPlan(
                title="Test",
                output_path=str(root / "final.mp4"),
                scenes=[
                    LocalSceneAsset("S01", str(img1), 2.0, str(audio)),
                    LocalSceneAsset("S02", str(img2), 3.0, ""),
                ],
                subtitles_path=str(captions),
            )
            self.assertEqual(plan.validate(), [])
            built = build_render_commands(plan, work_dir=root / "work")
            self.assertEqual(len(built["segments"]), 2)
            self.assertEqual(len(built["commands"]), 4)
            self.assertFalse(built["copy_assembled_to_final"])
            self.assertTrue(all(cmd[0] == "ffmpeg" for cmd in built["commands"]))

    def test_render_plan_accepts_local_blender_video_clip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clip = root / "blender.mp4"
            clip.write_bytes(b"x")
            plan = LocalRenderPlan(
                title="Blender handoff",
                output_path=str(root / "final.mp4"),
                scenes=[
                    LocalSceneAsset(
                        "S01",
                        "",
                        4.0,
                        "",
                        video_path=str(clip),
                    )
                ],
            )
            self.assertEqual(plan.validate(), [])
            built = build_render_commands(plan, work_dir=root / "work")
            first = built["commands"][0]
            self.assertEqual(first[0], "ffmpeg")
            self.assertIn("-stream_loop", first)
            self.assertIn(str(clip), first)

    def test_render_plan_rejects_image_and_video_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "frame.png"
            video = root / "clip.mp4"
            image.write_bytes(b"x")
            video.write_bytes(b"x")
            plan = LocalRenderPlan(
                title="Ambiguous",
                output_path=str(root / "final.mp4"),
                scenes=[
                    LocalSceneAsset(
                        "S01",
                        str(image),
                        2.0,
                        "",
                        video_path=str(video),
                    )
                ],
            )
            self.assertTrue(plan.validate())

    def test_render_plan_rejects_missing_assets(self):
        plan = LocalRenderPlan(
            title="Bad",
            output_path="out.mp4",
            scenes=[LocalSceneAsset("S01", "missing.png", 2.0)],
        )
        self.assertTrue(plan.validate())


if __name__ == "__main__":
    unittest.main()
