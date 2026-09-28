from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import zipfile

from servicebridge.local_runtime.archive import safe_extract_zip


class SafeArchiveTests(unittest.TestCase):
    def test_extracts_normal_members(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("meshes/a.obj", b"mesh")
        buf.seek(0)

        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(buf) as zf:
                safe_extract_zip(zf, directory)
            self.assertEqual(
                (Path(directory) / "meshes" / "a.obj").read_bytes(),
                b"mesh",
            )

    def test_blocks_parent_traversal(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../escape.txt", b"nope")
        buf.seek(0)

        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(buf) as zf:
                with self.assertRaises(ValueError):
                    safe_extract_zip(zf, directory)

    def test_blocks_absolute_path(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("/absolute.txt", b"nope")
        buf.seek(0)

        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(buf) as zf:
                with self.assertRaises(ValueError):
                    safe_extract_zip(zf, directory)


if __name__ == "__main__":
    unittest.main()
