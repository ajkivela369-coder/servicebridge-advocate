import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "apps" / "medforge-imaging-studio"

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

masks = load_module("medforge_masks_test", "med_masks.py")


def nifti_bytes(arr):
    affine = np.eye(4)
    img = nib.Nifti1Image(arr.astype(np.uint8), affine)
    with tempfile.NamedTemporaryFile(suffix=".nii.gz") as tmp:
        nib.save(img, tmp.name)
        return Path(tmp.name).read_bytes()


class MedForgeMaskTests(unittest.TestCase):
    def test_nifti_mask_import(self):
        arr = np.zeros((7, 8, 9), dtype=np.uint8)
        arr[2:5, 3:6, 4:7] = 1
        loaded = masks.load_mask_upload(nifti_bytes(arr), "organ.nii.gz", "test")
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].shape, (7, 8, 9))
        self.assertGreater(loaded[0].voxel_count, 0)
        self.assertEqual(loaded[0].provenance, "test")

    def test_zip_mask_import(self):
        raw1 = nifti_bytes(np.ones((4, 4, 4), dtype=np.uint8))
        raw2 = nifti_bytes(np.eye(4, dtype=np.uint8)[:, :, None].repeat(4, axis=2))
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("masks/a.nii.gz", raw1)
            zf.writestr("masks/b.nii.gz", raw2)
            zf.writestr("README.txt", "ignored")
        loaded = masks.load_mask_upload(buf.getvalue(), "masks.zip")
        self.assertEqual(len(loaded), 2)

    def test_alignment_never_allows_overlay_by_shape_alone(self):
        arr = np.ones((5, 5, 5), dtype=np.uint8)
        m = masks.load_mask_upload(nifti_bytes(arr), "mask.nii.gz")[0]
        note = masks.mask_alignment_note(m, (5, 5, 5))
        self.assertTrue(note["same_array_shape"])
        self.assertFalse(note["overlay_allowed"])
        self.assertIn("affine", note["reason"].lower())


if __name__ == "__main__":
    unittest.main()
