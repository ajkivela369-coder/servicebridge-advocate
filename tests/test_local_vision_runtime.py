from __future__ import annotations

import unittest

from servicebridge.local_runtime import RuntimeMode, RuntimePolicy
from servicebridge.local_runtime.vision import LocalVisionClient, build_vision_payload


class LocalVisionRuntimeTests(unittest.TestCase):
    def test_creditless_blocks_external_multimodal_endpoint(self):
        with self.assertRaises(PermissionError):
            LocalVisionClient(
                endpoint="https://api.example.com/v1/chat/completions",
                policy=RuntimePolicy(mode=RuntimeMode.CREDITLESS),
            )

    def test_payload_keeps_image_and_instruction_channels_separate(self):
        payload = build_vision_payload(
            model="local-vlm",
            image_data_uri="data:image/png;base64,AAAA",
            instructions="OBSERVE ONLY",
            question="What is visible?",
        )
        self.assertEqual(payload["model"], "local-vlm")
        self.assertEqual(payload["messages"][0]["role"], "system")
        user_content = payload["messages"][1]["content"]
        self.assertEqual(user_content[0]["type"], "text")
        self.assertEqual(user_content[1]["type"], "image_url")
        self.assertTrue(
            user_content[1]["image_url"]["url"].startswith("data:image/png;base64,")
        )

    def test_payload_rejects_non_image_data_uri(self):
        with self.assertRaises(ValueError):
            build_vision_payload(
                model="local-vlm",
                image_data_uri="https://example.com/scan.png",
                instructions="OBSERVE ONLY",
                question="What is visible?",
            )


if __name__ == "__main__":
    unittest.main()
