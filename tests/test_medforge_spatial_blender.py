import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MED = ROOT / "apps" / "medforge-imaging-studio"
if str(MED) not in sys.path:
    sys.path.insert(0, str(MED))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, MED / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


space = load("med_space_test", "med_space.py")
mesh_mod = load("med_mesh_test", "med_mesh.py")
masks_mod = load("med_masks_mesh_test", "med_masks.py")
motion_mod = load("med_motion_test", "med_motion.py")
blender_mod = load("med_blender_test", "med_blender.py")
native_mod = load("med_native3d_test", "med_native3d.py")


class MedForgeSpatialTests(unittest.TestCase):
    def setUp(self):
        # MedForge source array axes are z,y,x. This affine maps them to RAS mm.
        self.source_shape = (5, 8, 10)
        self.source_affine = np.array([
            [0.0, 0.0, -0.9, 12.0],
            [0.0, -0.8, 0.0, 30.0],
            [1.5, 0.0, 0.0, -20.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def test_same_geometry_is_overlay_ready(self):
        report = space.alignment_report(
            self.source_shape,
            self.source_affine,
            self.source_shape,
            self.source_affine,
        )
        self.assertTrue(report.spatial_overlay_ready)
        self.assertAlmostEqual(report.physical_overlap_ratio, 1.0, places=6)
        self.assertAlmostEqual(report.center_distance_mm, 0.0, places=6)

    def test_reoriented_nifti_resamples_back_to_source_grid(self):
        source_mask = np.zeros(self.source_shape, dtype=bool)
        source_mask[1:4, 2:6, 3:8] = True

        # Mask file axes are x,y,z instead of z,y,x.
        mask_data = np.transpose(source_mask, (2, 1, 0))
        permutation = np.array([
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        mask_affine = self.source_affine @ permutation

        aligned, report = space.resample_mask_to_source(
            mask_data,
            mask_affine,
            self.source_shape,
            self.source_affine,
        )
        self.assertTrue(report.spatial_overlay_ready)
        np.testing.assert_array_equal(aligned, source_mask)

    def test_distant_mask_is_blocked(self):
        far_affine = self.source_affine.copy()
        far_affine[:3, 3] += np.array([1000.0, 1000.0, 1000.0])
        report = space.alignment_report(
            self.source_shape,
            self.source_affine,
            self.source_shape,
            far_affine,
        )
        self.assertFalse(report.spatial_overlay_ready)
        self.assertEqual(report.physical_overlap_ratio, 0.0)


class MedForgeMeshBlenderTests(unittest.TestCase):
    def make_mask(self, name="vertebra.nii.gz"):
        data = np.zeros((16, 16, 16), dtype=bool)
        data[4:12, 5:11, 3:13] = True
        affine = np.diag([0.8, 0.9, 1.2, 1.0])
        return masks_mod.MaskVolume(
            name=name,
            data=data,
            affine=affine,
            source_format="NIfTI",
            provenance="synthetic unit-test mask",
        )

    def test_mask_to_patient_space_mesh_and_obj(self):
        mask = self.make_mask()
        mesh = mesh_mod.mask_to_mesh(
            mask.data,
            mask.affine,
            name=mask.name,
            provenance=mask.provenance,
            step_size=1,
        )
        self.assertGreater(len(mesh.vertices_ras_mm), 0)
        self.assertGreater(len(mesh.faces), 0)
        self.assertGreater(mesh_mod.mesh_surface_area_mm2(mesh), 0)
        obj = mesh_mod.mesh_to_obj(mesh).decode("utf-8")
        self.assertIn("DERIVED / UNREVIEWED", obj)
        self.assertIn("\nv ", "\n" + obj)
        self.assertIn("\nf ", "\n" + obj)

    def test_singular_affine_is_rejected_before_mesh_export(self):
        mask = self.make_mask()
        singular = mask.affine.copy()
        singular[:3, 2] = 0.0
        with self.assertRaises(ValueError):
            mesh_mod.mask_to_mesh(
                mask.data,
                singular,
                name=mask.name,
                provenance=mask.provenance,
            )

    def test_motion_is_explicitly_illustrative(self):
        motion = motion_mod.build_motion(
            "vertebra",
            translation_mm_xyz=(1.0, 2.0, 3.0),
            rotation_deg_xyz=(0.0, 5.0, 0.0),
            note="synthetic test",
        )
        self.assertIn("ILLUSTRATIVE", motion.evidence_lane)
        self.assertEqual(motion.translation_mm_xyz[1], 2.0)
        restored = motion_mod.motion_from_dict(motion.to_dict())
        self.assertEqual(restored, motion)

    def test_blender_bundle_is_self_contained_and_has_no_dicom(self):
        mask = self.make_mask()
        object_id = blender_mod.object_ids_for_masks([mask])[0]
        motion = motion_mod.build_motion(
            object_id,
            translation_mm_xyz=(0.0, 1.0, 0.0),
            rotation_deg_xyz=(0.0, 0.0, 3.0),
        )
        bundle = blender_mod.build_blender_scene_bundle(
            [mask],
            [motion],
            mesh_step_size=2,
        )
        with zipfile.ZipFile(BytesIO(bundle)) as zf:
            names = set(zf.namelist())
            self.assertIn("scene.json", names)
            self.assertIn("blender_medforge_scene.py", names)
            self.assertIn(f"meshes/{object_id}.obj", names)
            self.assertFalse(any(x.lower().endswith(".dcm") for x in names))
            scene = __import__("json").loads(zf.read("scene.json"))
            self.assertFalse(scene["evidence_rules"]["source_dicom_included"])
            self.assertFalse(scene["evidence_rules"]["motion_is_inferred_by_software"])
            self.assertEqual(scene["motions"][0]["structure_id"], object_id)
            blender_script = zf.read("blender_medforge_scene.py").decode("utf-8")
            self.assertIn("ILLUSTRATIVE / DERIVED", blender_script)
            self.assertIn("use_stamp_note", blender_script)

    def test_native_motion_math_uses_same_explicit_track(self):
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ])
        motion = motion_mod.build_motion(
            "vertebra",
            translation_mm_xyz=(4.0, 0.0, 0.0),
            rotation_deg_xyz=(0.0, 0.0, 0.0),
            start_frame=1,
            end_frame=5,
        )
        halfway = native_mod.transform_vertices(vertices, motion, 3)
        np.testing.assert_allclose(halfway, vertices + np.array([2.0, 0.0, 0.0]))
        final = native_mod.transform_vertices(vertices, motion, 5)
        np.testing.assert_allclose(final, vertices + np.array([4.0, 0.0, 0.0]))

    def test_native_rotation_occurs_about_mesh_center(self):
        vertices = np.array([
            [-1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        motion = motion_mod.build_motion(
            "vertebra",
            rotation_deg_xyz=(0.0, 0.0, 90.0),
            start_frame=1,
            end_frame=2,
        )
        rotated = native_mod.transform_vertices(vertices, motion, 2)
        np.testing.assert_allclose(
            rotated,
            np.array([[0.0, -1.0, 0.0], [0.0, 1.0, 0.0]]),
            atol=1e-6,
        )

    def test_blender_command_is_background_local(self):
        command = blender_mod.blender_bundle_command(
            "/tmp/bundle",
            render_video=True,
        )
        self.assertEqual(command[0], "blender")
        self.assertIn("--background", command)
        self.assertIn("--render", command)


if __name__ == "__main__":
    unittest.main()
