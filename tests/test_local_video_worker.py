from __future__ import annotations

import inspect
import unittest

from servicebridge.local_runtime.video import _supported_call_kwargs


class LocalVideoWorkerTests(unittest.TestCase):
    def test_filters_model_specific_parameters(self):
        def pipeline(prompt, width, height, num_frames, generator=None):
            return None

        candidates = {
            "prompt": "test",
            "negative_prompt": "bad",
            "width": 768,
            "height": 512,
            "num_frames": 49,
            "num_inference_steps": 30,
            "guidance_scale": 6.0,
            "generator": object(),
        }
        filtered = _supported_call_kwargs(pipeline, candidates)
        self.assertEqual(
            set(filtered),
            {"prompt", "width", "height", "num_frames", "generator"},
        )

    def test_var_keyword_pipeline_can_receive_generic_profile(self):
        def pipeline(prompt, **kwargs):
            return None

        candidates = {
            "prompt": "test",
            "negative_prompt": None,
            "num_frames": 49,
            "guidance_scale": 6.0,
        }
        filtered = _supported_call_kwargs(pipeline, candidates)
        self.assertEqual(filtered["prompt"], "test")
        self.assertEqual(filtered["num_frames"], 49)
        self.assertNotIn("negative_prompt", filtered)


if __name__ == "__main__":
    unittest.main()
