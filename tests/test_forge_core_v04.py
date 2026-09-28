from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_core.scheduler import (
    FitStatus,
    MemoryAdmissionController,
    ReservationStore,
    ResourceRequest,
    WorkClass,
    choose_model,
)
from forge_core.vault import ForgeVault
from servicebridge.local_runtime.models import LocalModel
from servicebridge.local_runtime.runtime import HardwareProfile


def hw(
    *,
    ram_total=16.0,
    ram_free=12.0,
    vram_total=8.0,
    vram_free=7.0,
):
    return HardwareProfile(
        os="TestOS",
        machine="x86_64",
        cpu_count=8,
        ram_gb=ram_total,
        gpu_name="Test GPU" if vram_total else None,
        gpu_vram_gb=vram_total if vram_total else None,
        nvidia_smi=bool(vram_total),
        tier="test",
        ram_available_gb=ram_free,
        gpu_vram_free_gb=vram_free if vram_total else None,
    )


class ForgeMemoryAdmissionTests(unittest.TestCase):
    def test_safe_tight_blocked_are_enforced_from_live_free_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            with ReservationStore(Path(directory) / "leases.sqlite3") as leases:
                controller = MemoryAdmissionController(leases)
                safe = controller.assess(
                    ResourceRequest("reason", ram_gb=2, vram_gb=2),
                    hardware=hw(),
                )
                self.assertEqual(safe.status, FitStatus.SAFE)

                blocked = controller.assess(
                    ResourceRequest(
                        "vision",
                        ram_gb=11,
                        vram_gb=7,
                        allow_cpu_fallback=False,
                    ),
                    hardware=hw(),
                )
                self.assertEqual(blocked.status, FitStatus.BLOCKED)

    def test_pending_reservation_reduces_next_apps_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            with ReservationStore(Path(directory) / "leases.sqlite3") as leases:
                controller = MemoryAdmissionController(leases)
                before = controller.budget(hw())
                leases.reserve(
                    "model:grimforge:vision",
                    owner="grimforge",
                    capability="vision",
                    model_id="vlm",
                    ram_gb=2.0,
                    vram_gb=3.0,
                )
                after = controller.budget(hw())
                self.assertAlmostEqual(
                    before["usable_ram_gb"] - after["usable_ram_gb"],
                    2.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    before["usable_vram_gb"] - after["usable_vram_gb"],
                    3.0,
                    places=6,
                )

    def test_cpu_fallback_charges_gpu_requirement_to_host_ram(self):
        with tempfile.TemporaryDirectory() as directory:
            with ReservationStore(Path(directory) / "leases.sqlite3") as leases:
                controller = MemoryAdmissionController(leases)
                decision = controller.assess(
                    ResourceRequest(
                        "vision",
                        ram_gb=2.0,
                        vram_gb=5.0,
                        allow_cpu_fallback=True,
                    ),
                    hardware=hw(ram_free=14.0, vram_free=1.5),
                )
                self.assertEqual(decision.status, FitStatus.TIGHT)
                self.assertFalse(decision.use_gpu)
                self.assertEqual(decision.vram_required_gb, 0.0)
                self.assertAlmostEqual(decision.ram_required_gb, 7.0, places=6)

    def test_model_router_skips_higher_quality_model_that_does_not_fit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            large_path = root / "large.gguf"
            small_path = root / "small.gguf"
            large_path.write_bytes(b"x")
            small_path.write_bytes(b"x")
            models = [
                LocalModel(
                    "large",
                    "text",
                    str(large_path),
                    quality_rank=100,
                    min_ram_gb=20.0,
                    min_vram_gb=12.0,
                ),
                LocalModel(
                    "small",
                    "text",
                    str(small_path),
                    quality_rank=50,
                    min_ram_gb=3.0,
                    min_vram_gb=2.0,
                ),
            ]
            with ReservationStore(root / "leases.sqlite3") as leases:
                controller = MemoryAdmissionController(leases)
                selected, decision = choose_model(
                    models,
                    controller,
                    capability="reason",
                    work_class=WorkClass.STANDARD,
                    requester="elias",
                    hardware=hw(),
                )
                self.assertEqual(selected.model_id, "small")
                self.assertIn(decision.status, {FitStatus.SAFE, FitStatus.TIGHT})


class ForgeVaultTests(unittest.TestCase):
    def test_same_original_is_stored_once_and_referenced_by_multiple_apps(self):
        with tempfile.TemporaryDirectory() as directory:
            with ForgeVault(directory) as vault:
                first = vault.add_bytes(
                    b"same evidence bytes",
                    original_name="record.pdf",
                )
                second = vault.add_bytes(
                    b"same evidence bytes",
                    original_name="copy-of-record.pdf",
                )
                self.assertEqual(first["source_id"], second["source_id"])
                self.assertEqual(first["sha256"], second["sha256"])

                vault.reference("evidence_auditor", first["source_id"])
                vault.reference("medforge", first["source_id"])
                refs = vault.references_for(first["source_id"])
                self.assertEqual(
                    {x["app_id"] for x in refs},
                    {"evidence_auditor", "medforge"},
                )
                self.assertEqual(vault.status()["source_count"], 1)
                self.assertEqual(vault.status()["reference_count"], 2)


class OneBackendFourAppsTests(unittest.TestCase):
    def test_four_primary_apps_depend_on_forge_sdk(self):
        repo = Path(__file__).resolve().parents[1]
        targets = {
            "elias": repo / "src/servicebridge/api.py",
            "evidence_auditor": repo / "portfolio/evidence-auditor/legacy-streamlit/dashboard.py",
            "medforge": repo / "apps/medforge-imaging-studio/app.py",
            "grimforge": repo / "apps/grimforge-war-theater/local_pipeline.py",
        }
        for app_id, path in targets.items():
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                "ForgeSDK",
                text,
                msg=f"{app_id} is no longer allowed to own a separate model/provider stack",
            )

    def test_medforge_does_not_expose_its_own_vlm_endpoint_controls(self):
        repo = Path(__file__).resolve().parents[1]
        text = (repo / "apps/medforge-imaging-studio/app.py").read_text(encoding="utf-8")
        self.assertNotIn('st.text_input(\n            "Local endpoint"', text)
        self.assertIn("Analyze source through Forge", text)

    def test_grimforge_pipeline_uses_forge_for_tts_and_final_render(self):
        repo = Path(__file__).resolve().parents[1]
        text = (repo / "apps/grimforge-war-theater/local_pipeline.py").read_text(encoding="utf-8")
        self.assertIn('ForgeSDK.for_app("grimforge").render_video', text)
        self.assertIn("forge.tts(", text)
        self.assertNotIn("generate_speech_local_auto(", text)


if __name__ == "__main__":
    unittest.main()
