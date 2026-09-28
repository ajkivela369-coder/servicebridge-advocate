from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from servicebridge.local_runtime.offline import build_offline_pack, verify_offline_pack


class OfflinePackTests(unittest.TestCase):
    def test_pack_whitelists_code_and_excludes_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "safe.py").write_text("print('safe')")
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# guide")
            (root / "private_data").mkdir()
            (root / "private_data" / "evidence.sqlite3").write_bytes(b"SECRET")
            (root / ".env").write_text("API_KEY=SECRET")
            (root / "random.bin").write_bytes(b"PRIVATE")

            out = root / "pack.zip"
            result = build_offline_pack(out, repo_root=root)
            self.assertGreaterEqual(result["repo_files"], 2)

            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
                self.assertIn("repo/src/safe.py", names)
                self.assertIn("repo/docs/guide.md", names)
                self.assertNotIn("repo/private_data/evidence.sqlite3", names)
                self.assertNotIn("repo/.env", names)
                self.assertFalse(any("random.bin" in name for name in names))

            verified = verify_offline_pack(out)
            self.assertTrue(verified["ok"])

    def test_models_require_explicit_include_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "safe.py").write_text("pass")
            model = root / "model.gguf"
            model.write_bytes(b"MODEL")
            catalog = root / "models.json"
            catalog.write_text(json.dumps({
                "models": [{
                    "model_id": "test-model",
                    "kind": "text",
                    "path": str(model),
                    "format": "gguf",
                    "quality_rank": 1,
                    "min_ram_gb": 0,
                    "min_vram_gb": 0,
                    "sha256": "",
                    "notes": "",
                }]
            }))

            no_models = root / "no-models.zip"
            build_offline_pack(
                no_models,
                repo_root=root,
                model_catalog=catalog,
                include_models=False,
            )
            with zipfile.ZipFile(no_models) as zf:
                self.assertFalse(any(name.startswith("models/") for name in zf.namelist()))

            with_models = root / "with-models.zip"
            build_offline_pack(
                with_models,
                repo_root=root,
                model_catalog=catalog,
                include_models=True,
            )
            with zipfile.ZipFile(with_models) as zf:
                self.assertIn("models/test-model/model.gguf", zf.namelist())


if __name__ == "__main__":
    unittest.main()
