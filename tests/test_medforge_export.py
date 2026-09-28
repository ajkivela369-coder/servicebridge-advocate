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

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

masks_mod = load("medforge_masks_export_test", "med_masks.py")
export_mod = load("medforge_export_test", "med_export.py")


def mask_obj():
    arr = np.zeros((6, 7, 8), dtype=np.uint8)
    arr[1:5, 2:6, 3:7] = 1
    img = nib.Nifti1Image(arr, np.diag([1.2, 1.3, 1.4, 1.0]))
    with tempfile.NamedTemporaryFile(suffix=".nii.gz") as tmp:
        nib.save(img, tmp.name)
        raw = Path(tmp.name).read_bytes()
    return masks_mod.load_mask_upload(raw, "test-mask.nii.gz", "unit-test")[0]


class MedForgeExportTests(unittest.TestCase):
    def test_bundle_contains_manifest_mask_and_no_dicom(self):
        bundle = export_mod.build_render_bundle(
            manifest={"title": "Test", "stage": "planned"},
            masks=[mask_obj()],
            include_source_preview=False,
        )
        with zipfile.ZipFile(BytesIO(bundle)) as zf:
            names = set(zf.namelist())
            self.assertIn("medforge-render-manifest.json", names)
            self.assertIn("masks/test-mask.nii.gz", names)
            self.assertIn("README_EVIDENCE_BOUNDARIES.txt", names)
            self.assertFalse(any(name.lower().endswith(".dcm") for name in names))

    def test_exported_nifti_preserves_affine(self):
        m = mask_obj()
        raw = export_mod.nifti_mask_bytes(m)
        with tempfile.NamedTemporaryFile(suffix=".nii.gz") as tmp:
            tmp.write(raw)
            tmp.flush()
            restored = nib.load(tmp.name)
            np.testing.assert_allclose(restored.affine, m.affine)


if __name__ == "__main__":
    unittest.main()
