from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from servicebridge.local_runtime import (
    AssetCache,
    JobQueue,
    LocalOpenAICompatibleProvider,
    RuntimeMode,
    RuntimePolicy,
)
from servicebridge.local_runtime.media import (
    burn_subtitles_command,
    concat_command,
    image_sequence_command,
    mux_audio_command,
    still_to_video_command,
)
from servicebridge.local_runtime.memory import LocalEmbeddingClient, LocalVectorStore, cosine_similarity
from servicebridge.local_runtime.documents import _collect_text
from servicebridge.local_runtime.gateway import GatewayConfig
from servicebridge.providers import provider_for_runtime


class LocalRuntimePolicyTests(unittest.TestCase):
    def test_creditless_allows_loopback(self):
        policy = RuntimePolicy(mode=RuntimeMode.CREDITLESS)
        for url in (
            "http://127.0.0.1:8080/v1/chat/completions",
            "http://localhost:8188/prompt",
            "http://[::1]:11434/api/tags",
        ):
            policy.assert_url_allowed(url)

    def test_creditless_blocks_external_even_if_external_flag_is_true(self):
        policy = RuntimePolicy(
            mode=RuntimeMode.CREDITLESS,
            allow_external_network=True,
            allow_cloud_fallback=True,
        )
        with self.assertRaises(PermissionError):
            policy.assert_url_allowed("https://api.example.com/v1/chat")

    def test_hybrid_requires_explicit_external_network_permission(self):
        policy = RuntimePolicy(mode=RuntimeMode.HYBRID)
        with self.assertRaises(PermissionError):
            policy.assert_url_allowed("https://api.example.com/v1/chat")

    def test_cloud_allowed_only_when_both_flags_are_explicit(self):
        self.assertFalse(
            RuntimePolicy(
                mode=RuntimeMode.CLOUD,
                allow_external_network=True,
                allow_cloud_fallback=False,
            ).cloud_allowed
        )
        self.assertTrue(
            RuntimePolicy(
                mode=RuntimeMode.CLOUD,
                allow_external_network=True,
                allow_cloud_fallback=True,
            ).cloud_allowed
        )

    def test_creditless_provider_is_local_client(self):
        provider = provider_for_runtime(mode=RuntimeMode.CREDITLESS)
        self.assertIsInstance(provider, LocalOpenAICompatibleProvider)
        self.assertTrue(provider.endpoint.startswith("http://127.0.0.1:"))


class LocalRuntimeStorageTests(unittest.TestCase):
    def test_asset_cache_deduplicates_identical_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            with AssetCache(Path(tmp) / "vault") as cache:
                a = cache.put(b"same bytes", kind="text", suffix=".txt")
                b = cache.put(b"same bytes", kind="text", suffix=".txt")
                self.assertEqual(a["asset_id"], b["asset_id"])
                self.assertEqual(a["sha256"], b["sha256"])
                self.assertTrue(Path(a["path"]).exists())

    def test_job_queue_persists_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = JobQueue(Path(tmp) / "jobs.sqlite3")
            job_id = queue.enqueue("render", {"scene": 4})
            self.assertEqual(queue.get(job_id)["status"], "queued")
            queue.update(job_id, "completed", {"output": "scene04.mp4"})
            job = queue.get(job_id)
            self.assertEqual(job["status"], "completed")
            self.assertEqual(job["result"]["output"], "scene04.mp4")
            queue.close()


class LocalRuntimeMediaTests(unittest.TestCase):
    def test_still_video_command_is_local_ffmpeg(self):
        command = still_to_video_command("frame.png", "out.mp4", duration=3.5)
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("frame.png", command)
        self.assertIn("out.mp4", command)
        self.assertIn("3.500", command)

    def test_concat_command_is_local_ffmpeg(self):
        command = concat_command("concat.txt", "movie.mp4")
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("concat.txt", command)
        self.assertIn("movie.mp4", command)

    def test_mux_caption_and_sequence_commands_stay_local(self):
        mux = mux_audio_command("video.mp4", "voice.wav", "mixed.mp4")
        caps = burn_subtitles_command("mixed.mp4", "captions.srt", "captioned.mp4")
        seq = image_sequence_command("frame_%04d.png", "movie.mp4")
        self.assertEqual(mux[0], "ffmpeg")
        self.assertEqual(caps[0], "ffmpeg")
        self.assertEqual(seq[0], "ffmpeg")
        self.assertTrue(any(x.startswith("loudnorm=I=-16") for x in mux))
        self.assertTrue(any("subtitles=" in x for x in caps))


class LocalRuntimeMemoryTests(unittest.TestCase):
    def test_cosine_similarity_and_local_vector_store(self):
        self.assertAlmostEqual(cosine_similarity([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1, 0], [0, 1]), 0.0)
        with tempfile.TemporaryDirectory() as tmp:
            with LocalVectorStore(Path(tmp) / "vectors.sqlite3") as store:
                store.upsert("a", "alpha", [1, 0], {"source": "A"})
                store.upsert("b", "beta", [0, 1], {"source": "B"})
                hits = store.search([0.9, 0.1], limit=2)
                self.assertEqual(hits[0].item_id, "a")
                self.assertEqual(hits[0].metadata["source"], "A")

    def test_embedding_client_creditless_blocks_external_endpoint(self):
        with self.assertRaises(PermissionError):
            LocalEmbeddingClient(
                endpoint="https://api.example.com/v1/embeddings",
                policy=RuntimePolicy(mode=RuntimeMode.CREDITLESS),
            )

    def test_ocr_text_collector_handles_current_result_shape(self):
        payload = {
            "res": {
                "rec_texts": ["first line", "second line"],
                "nested": {"rec_text": "third line"},
            }
        }
        self.assertEqual(
            _collect_text(payload),
            ["first line", "second line", "third line"],
        )


class LocalRuntimeGatewayTests(unittest.TestCase):
    def test_gateway_defaults_to_creditless_loopback(self):
        cfg = GatewayConfig()
        self.assertEqual(cfg.mode, RuntimeMode.CREDITLESS)
        cfg.policy().assert_url_allowed("http://127.0.0.1:8080/v1/chat/completions")
        with self.assertRaises(PermissionError):
            cfg.policy().assert_url_allowed("https://api.example.com/v1/chat")


if __name__ == "__main__":
    unittest.main()
