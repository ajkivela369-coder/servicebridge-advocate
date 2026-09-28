from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_core.cache import ForgeProjectCache, stable_cache_key


class ForgeProjectCacheTests(unittest.TestCase):
    def test_same_project_payload_reuses_cached_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {"episode": {"title": "A", "scenes": [1, 2]}, "fps": 30}
            with ForgeProjectCache(directory) as cache:
                first = cache.put_bytes(
                    "grimforge-local-render",
                    payload,
                    b"video-bytes",
                    kind="grimforge-render",
                    suffix=".mp4",
                )
                hit = cache.get("grimforge-local-render", payload)
                self.assertIsNotNone(hit)
                self.assertEqual(first["cache_key"], hit["cache_key"])
                self.assertEqual(Path(hit["asset"]["path"]).read_bytes(), b"video-bytes")
                self.assertTrue(hit["hit"])

    def test_cache_key_is_order_independent_for_dicts(self):
        a = stable_cache_key("x", {"a": 1, "b": 2})
        b = stable_cache_key("x", {"b": 2, "a": 1})
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
