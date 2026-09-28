import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile

import numpy as np
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

ROOT = Path(__file__).resolve().parents[1] / "apps" / "medforge-imaging-studio"

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

volume_engine = load_module("medforge_volume_test", "med_volume.py")
seg_engine = load_module("medforge_seg_test", "med_segmentation.py")


def make_slice(series_uid, instance, z, value, rows=8, cols=10):
    file_meta = Dataset()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = generate_uid()
    ds.Modality = "CT"
    ds.SeriesDescription = "Synthetic public-style test series"
    ds.PatientName = "SHOULD^NOT^LEAK"
    ds.PatientID = "SECRET-ID"
    ds.Rows = rows
    ds.Columns = cols
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.PixelSpacing = [0.8, 0.9]
    ds.SliceThickness = 1.5
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = [0, 0, float(z)]
    ds.InstanceNumber = instance
    ds.RescaleSlope = 1
    ds.RescaleIntercept = -1000
    arr = np.full((rows, cols), int(value), dtype=np.int16)
    ds.PixelData = arr.tobytes()
    buf = BytesIO()
    ds.save_as(buf, enforce_file_format=True)
    return buf.getvalue()


class MedForgeVolumeTests(unittest.TestCase):
    def test_series_build_and_safe_summary(self):
        uid = generate_uid()
        blobs = [
            (f"slice-{i}.dcm", make_slice(uid, i + 1, i * 1.5, 100 + i))
            for i in range(5)
        ]
        infos = volume_engine.inspect_dicom_series(blobs)
        self.assertEqual(len(infos), 1)
        self.assertEqual(infos[0].instance_count, 5)

        study = volume_engine.build_dicom_volume(blobs, uid)
        self.assertEqual(study.shape, (5, 8, 10))
        self.assertAlmostEqual(study.spacing_zyx[0], 1.5, places=4)
        self.assertIsNotNone(study.affine_zyx_ras)
        expected_affine = np.array([
            [0.0, 0.0, -0.9, 0.0],
            [0.0, -0.8, 0.0, 0.0],
            [1.5, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        np.testing.assert_allclose(study.affine_zyx_ras, expected_affine, atol=1e-6)
        self.assertTrue(study.safe_summary()["spatial_affine_present"])
        summary_text = str(study.safe_summary())
        self.assertNotIn("SHOULD", summary_text)
        self.assertNotIn("SECRET-ID", summary_text)
        self.assertFalse(study.safe_summary()["raw_dicom_headers_retained"])

    def test_mpr_shapes(self):
        v = np.zeros((5, 8, 10), dtype=np.float32)
        a, c, s = volume_engine.mpr_slices(v, 2, 4, 5)
        self.assertEqual(a.shape, (8, 10))
        self.assertEqual(c.shape, (5, 10))
        self.assertEqual(s.shape, (5, 8))

    def test_zip_expansion(self):
        uid = generate_uid()
        raw = make_slice(uid, 1, 0, 100)
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("nested/slice.dcm", raw)
        expanded = volume_engine.expand_dicom_blobs([("study.zip", buf.getvalue())])
        self.assertEqual(len(expanded), 1)
        self.assertEqual(expanded[0][0], "slice.dcm")

    def test_mask_pipeline_is_explicitly_non_anatomical(self):
        v = np.arange(1000, dtype=np.float32).reshape(10, 10, 10)
        mask = seg_engine.percentile_mask(v, 90)
        summary = seg_engine.summarize_mask(mask)
        self.assertGreater(summary.voxel_count, 0)
        self.assertIn("not an anatomical", summary.note)
        self.assertFalse(seg_engine.totalsegmentator_job_spec()["diagnosis_claim"])


if __name__ == "__main__":
    unittest.main()
