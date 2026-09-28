import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "medforge_segment_local.py"
spec = importlib.util.spec_from_file_location("medforge_local_worker_test", SCRIPT)
worker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = worker
assert spec.loader is not None
spec.loader.exec_module(worker)


class MedForgeLocalWorkerTests(unittest.TestCase):
    def test_ct_command(self):
        cmd = worker.build_command(
            Path("ct.zip"), Path("out"), "CT", True, "cpu", ["vertebrae_C1", "vertebrae_C2"]
        )
        self.assertIn("--fast", cmd)
        self.assertIn("total", cmd)
        self.assertIn("--roi_subset", cmd)
        self.assertIn("vertebrae_C1", cmd)

    def test_mr_command(self):
        cmd = worker.build_command(
            Path("mr.nii.gz"), Path("out"), "MR", False, None, []
        )
        self.assertIn("total_mr", cmd)
        self.assertNotIn("--fast", cmd)


if __name__ == "__main__":
    unittest.main()
