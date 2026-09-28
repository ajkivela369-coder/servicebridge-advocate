import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image
from pydicom import examples

ROOT = Path(__file__).resolve().parents[1] / "apps" / "medforge-imaging-studio"

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

med_io = load_module("medforge_io", "med_io.py")


class MedForgeIOTests(unittest.TestCase):
    def test_png_ingestion(self):
        img = Image.fromarray(np.arange(64, dtype=np.uint8).reshape(8, 8)).convert("L")
        buf = BytesIO()
        img.save(buf, format="PNG")
        loaded = med_io.load_standard_image_bytes(buf.getvalue(), "sample.png")
        self.assertEqual((loaded.width, loaded.height), (8, 8))
        self.assertEqual(loaded.image.mode, "RGB")
        self.assertFalse(loaded.raw_dicom_headers_retained)

    def test_public_pydicom_ct_example(self):
        path = examples.get_path("ct")
        loaded = med_io.load_dicom_bytes(Path(path).read_bytes(), "CT_small.dcm")
        self.assertEqual(loaded.modality, "CT")
        self.assertGreater(loaded.width, 0)
        self.assertGreater(loaded.height, 0)
        self.assertFalse(loaded.raw_dicom_headers_retained)

    def test_public_pydicom_mr_example(self):
        path = examples.get_path("mr")
        loaded = med_io.load_dicom_bytes(Path(path).read_bytes(), "MR_small.dcm")
        self.assertEqual(loaded.modality, "MR")
        self.assertGreater(loaded.width, 0)
        self.assertGreater(loaded.height, 0)
        self.assertFalse(loaded.raw_dicom_headers_retained)


if __name__ == "__main__":
    unittest.main()
