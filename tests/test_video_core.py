import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "apps" / "video-core" / "pipeline.py"
SPEC = importlib.util.spec_from_file_location("video_core_pipeline", MODULE_PATH)
pipeline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pipeline
assert SPEC.loader is not None
SPEC.loader.exec_module(pipeline)


class VideoCoreTests(unittest.TestCase):
    def test_selects_connected_provider_that_supports_requested_fps(self):
        settings = pipeline.RenderSettings(fps=30)
        providers = [
            pipeline.ProviderCapabilities("offline", "video", connected=False, max_width=4096, max_height=2160),
            pipeline.ProviderCapabilities("small", "video", connected=True, max_width=1280, max_height=720, supported_fps=(24,)),
            pipeline.ProviderCapabilities("fit", "video", connected=True, max_width=1920, max_height=1080, supported_fps=(24, 30)),
        ]
        self.assertEqual(pipeline.select_provider(providers, "video", settings).provider_id, "fit")

    def test_qc_blocks_unknown_rights_and_missing_render(self):
        result = pipeline.run_qc(
            rights_basis="unknown",
            has_video=False,
            has_audio=True,
        )
        self.assertFalse(result.passed)
        self.assertFalse(result.checks["rights_known"])
        self.assertFalse(result.checks["video_present"])

    def test_export_ready_requires_rendered_stage_and_clean_qc(self):
        job = pipeline.RenderJob(
            job_id="job-1",
            app="wildtake",
            title="Demo",
            stage="rendered",
            rights_basis="owned",
        )
        qc = pipeline.run_qc(
            rights_basis="owned",
            has_video=True,
            has_audio=True,
        )
        self.assertTrue(qc.passed)
        self.assertTrue(pipeline.can_mark_export_ready(job, qc))


if __name__ == "__main__":
    unittest.main()
