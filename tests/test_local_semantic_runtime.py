from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from servicebridge.ingest import ingest_file
from servicebridge.models import EvidenceClass
from servicebridge.store import EvidenceStore
from servicebridge.local_runtime import HardwareProfile
from servicebridge.local_runtime.evidence import LocalSemanticEvidenceStore
from servicebridge.local_runtime.memory import LocalVectorStore
from servicebridge.local_runtime.models import LocalModel, LocalModelCatalog


class FakeEmbedder:
    def embed(self, texts):
        out = []
        for text in texts:
            lower = text.lower()
            out.append([
                float(lower.count("migraine") + lower.count("headache")),
                float(lower.count("attendance") + lower.count("work")),
                float(lower.count("shoulder")),
            ])
        return out


class LocalSemanticEvidenceTests(unittest.TestCase):
    def test_hybrid_local_index_preserves_evidence_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = root / "migraine.txt"
            b = root / "shoulder.txt"
            a.write_text("Migraine symptoms repeatedly affected work attendance and pace.")
            b.write_text("Shoulder range of motion was documented during the visit.")

            source_a, chunks_a = ingest_file(a, EvidenceClass.CLINICAL_RECORD)
            source_b, chunks_b = ingest_file(b, EvidenceClass.CLINICAL_RECORD)

            with EvidenceStore(root / "evidence.sqlite3") as base:
                base.add_document(source_a, chunks_a)
                base.add_document(source_b, chunks_b)
                with LocalVectorStore(root / "vectors.sqlite3") as vectors:
                    hybrid = LocalSemanticEvidenceStore(base, vectors, FakeEmbedder())
                    self.assertEqual(hybrid.index(), len(chunks_a) + len(chunks_b))
                    hits = hybrid.search("headache work", limit=2)

            self.assertTrue(hits)
            self.assertEqual(hits[0].chunk.source_id, source_a.source_id)
            self.assertEqual(hits[0].chunk.evidence_class, EvidenceClass.CLINICAL_RECORD)


class LocalModelCatalogTests(unittest.TestCase):
    def test_catalog_selects_best_model_that_fits_hardware(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            small = root / "small.gguf"
            large = root / "large.gguf"
            small.write_bytes(b"small")
            large.write_bytes(b"large")

            catalog = LocalModelCatalog(root / "models.json")
            catalog.add(
                LocalModel(
                    model_id="small",
                    kind="text",
                    path=str(small),
                    quality_rank=1,
                    min_ram_gb=4,
                )
            )
            catalog.add(
                LocalModel(
                    model_id="large",
                    kind="text",
                    path=str(large),
                    quality_rank=2,
                    min_ram_gb=24,
                )
            )
            hw = HardwareProfile(
                os="Test",
                machine="x86_64",
                cpu_count=8,
                ram_gb=16,
                gpu_name=None,
                gpu_vram_gb=None,
                nvidia_smi=False,
                tier="cpu-local",
            )
            self.assertEqual(catalog.best("text", hw).model_id, "small")

    def test_catalog_never_treats_missing_file_as_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = LocalModelCatalog(root / "models.json")
            catalog.add(
                LocalModel(
                    model_id="missing",
                    kind="embedding",
                    path=str(root / "missing.gguf"),
                    quality_rank=99,
                )
            )
            hw = HardwareProfile(
                os="Test",
                machine="x86_64",
                cpu_count=4,
                ram_gb=64,
                gpu_name=None,
                gpu_vram_gb=None,
                nvidia_smi=False,
                tier="cpu-local",
            )
            self.assertIsNone(catalog.best("embedding", hw))


if __name__ == "__main__":
    unittest.main()
