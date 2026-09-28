import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "apps" / "medforge-build-lab"
MED = ROOT / "apps" / "medforge-imaging-studio"

for path in (str(LAB), str(MED)):
    if path not in sys.path:
        sys.path.insert(0, path)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

lessons = load("medforge_lessons_test", LAB / "lessons.py")
med_blender = load("medforge_blender_lesson_test", MED / "med_blender.py")
med_export = load("medforge_export_lesson_test", MED / "med_export.py")
med_io = load("medforge_io_lesson_test", MED / "med_io.py")
med_masks = load("medforge_masks_lesson_test", MED / "med_masks.py")
med_mesh = load("medforge_mesh_lesson_test", MED / "med_mesh.py")
med_motion = load("medforge_motion_lesson_test", MED / "med_motion.py")
med_native3d = load("medforge_native3d_lesson_test", MED / "med_native3d.py")
med_space = load("medforge_space_lesson_test", MED / "med_space.py")
med_volume = load("medforge_volume_lesson_test", MED / "med_volume.py")
med_segmentation = load("medforge_seg_lesson_test", MED / "med_segmentation.py")
med_engine = load("medforge_engine_lesson_test", MED / "med_engine.py")

MODULES = {
    "med_blender": med_blender,
    "med_export": med_export,
    "med_io": med_io,
    "med_masks": med_masks,
    "med_mesh": med_mesh,
    "med_motion": med_motion,
    "med_native3d": med_native3d,
    "med_space": med_space,
    "med_volume": med_volume,
    "med_segmentation": med_segmentation,
    "med_engine": med_engine,
}


class MedForgeBuildLabTests(unittest.TestCase):
    def test_every_lesson_points_to_live_medforge_code(self):
        self.assertGreaterEqual(len(lessons.LESSONS), 19)
        for lesson in lessons.LESSONS:
            self.assertIn(lesson["module"], MODULES)
            self.assertTrue(
                hasattr(MODULES[lesson["module"]], lesson["function"]),
                f'Missing {lesson["module"]}.{lesson["function"]}',
            )

    def test_pipeline_has_source_and_export_boundaries(self):
        self.assertEqual(lessons.PIPELINE[0], "Source")
        self.assertIn("Privacy", lessons.PIPELINE)
        self.assertIn("Mechanism", lessons.PIPELINE)
        self.assertIn("Spatial Alignment", lessons.PIPELINE)
        self.assertIn("Blender Scene", lessons.PIPELINE)
        self.assertIn("Native 3D Fallback", lessons.PIPELINE)
        self.assertIn("Render / Export", lessons.PIPELINE)


if __name__ == "__main__":
    unittest.main()
