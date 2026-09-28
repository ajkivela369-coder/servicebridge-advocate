from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import urllib.request

import numpy as np
from PIL import Image
from pydicom import examples

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "medforge-imaging-studio"
CACHE = ROOT / ".medforge-smoke"
CACHE.mkdir(exist_ok=True)

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, APP / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

med_io = load_module("medforge_io_smoke", "med_io.py")
med_engine = load_module("medforge_engine_smoke", "med_engine.py")

PUBLIC_DATASETS = [
    {
        "name": "MedMNIST BreastMNIST",
        "url": "https://zenodo.org/records/10519652/files/breastmnist.npz?download=1",
        "expected_md5": "750601b1f35ba3300ea97c75c52ff8f6",
        "kind": "npz",
        "source_note": "MedMNIST public benchmark; breast ultrasound-derived dataset",
    },
    {
        "name": "MedMNIST PneumoniaMNIST",
        "url": "https://zenodo.org/records/10519652/files/pneumoniamnist.npz?download=1",
        "expected_md5": "28209eda62fecd6e6a2d98b1501bb15f",
        "kind": "npz",
        "source_note": "MedMNIST public benchmark; pediatric chest X-ray-derived dataset",
    },
]

def download(item):
    target = CACHE / (item["name"].replace(" ", "_") + ".npz")
    if not target.exists():
        req = urllib.request.Request(item["url"], headers={"User-Agent": "MedForge-public-smoke/1.0"})
        with urllib.request.urlopen(req, timeout=90) as response, open(target, "wb") as out:
            out.write(response.read())
    digest = hashlib.md5(target.read_bytes()).hexdigest()
    if digest != item["expected_md5"]:
        raise RuntimeError(f"MD5 mismatch for {item['name']}: {digest}")
    return target

def npz_sample_to_png_bytes(path):
    data = np.load(path)
    for key in ("test_images", "val_images", "train_images"):
        if key in data and len(data[key]):
            arr = data[key][0]
            break
    else:
        raise RuntimeError(f"No image array found in {path}")
    arr = np.asarray(arr)
    if arr.ndim == 2:
        img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
    elif arr.ndim == 3 and arr.shape[-1] in (1, 3, 4):
        if arr.shape[-1] == 1:
            arr = arr[..., 0]
            img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
        else:
            img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
    else:
        raise RuntimeError(f"Unexpected 2D sample shape: {arr.shape}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), arr.shape

def exercise_pipeline(source_name, loaded, source_note):
    label = med_engine.ImageLabel(
        id="L01",
        name="Public smoke-test region",
        lane="Source observation",
        note="Synthetic label used only to test serialization and evidence-lane preservation.",
        x=50,
        y=50,
        confidence="Directly visible",
        source_ref=source_note,
    )
    steps = med_engine.build_mechanism_steps(
        loaded.modality,
        "labeled region",
        "Compression",
        "example motion used only for software testing",
        "example hypothetical downstream effect",
        source_name,
    )
    manifest = med_engine.build_render_manifest(source_name, loaded.source_name, [label], steps)

    assert manifest["render_rules"]["preserve_source_pixels"] is True
    assert manifest["render_rules"]["do_not_present_hypothesis_as_observation"] is True
    assert manifest["labels"][0]["lane"] == "Source observation"
    assert steps[0].epistemic_status == "SOURCE-OBSERVED"
    assert any("HYPOTH" in x.epistemic_status for x in steps)
    assert loaded.raw_dicom_headers_retained is False

    return {
        "source": source_name,
        "source_note": source_note,
        "modality": loaded.modality,
        "source_kind": loaded.source_kind,
        "width": loaded.width,
        "height": loaded.height,
        "raw_dicom_headers_retained": loaded.raw_dicom_headers_retained,
        "labels_serialized": len(manifest["labels"]),
        "mechanism_steps": len(manifest["mechanism_steps"]),
        "source_fidelity_rule": manifest["render_rules"]["preserve_source_pixels"],
        "hypothesis_separation_rule": manifest["render_rules"]["do_not_present_hypothesis_as_observation"],
        "status": "PASS",
    }

def main():
    results = []

    for item in PUBLIC_DATASETS:
        path = download(item)
        png_bytes, original_shape = npz_sample_to_png_bytes(path)
        loaded = med_io.load_standard_image_bytes(png_bytes, item["name"] + ".png")
        result = exercise_pipeline(item["name"], loaded, item["source_note"])
        result["original_sample_shape"] = list(original_shape)
        results.append(result)

    for key, display in [("ct", "pydicom public CT example"), ("mr", "pydicom public MR example")]:
        path = examples.get_path(key)
        loaded = med_io.load_dicom_bytes(Path(path).read_bytes(), Path(path).name)
        results.append(exercise_pipeline(display, loaded, "pydicom public example dataset"))

    # TCIA documents getSingleImage as a public API that returns one DICOM
    # object identified by SeriesInstanceUID + SOPInstanceUID.
    tcia_url = (
        "https://services.cancerimagingarchive.net/nbia-api/services/v1/getSingleImage"
        "?SeriesInstanceUID=143.284188174537413748743284550513035752067"
        "&SOPInstanceUID=143.53599064898089361503082484556513429004"
    )
    req = urllib.request.Request(tcia_url, headers={"User-Agent": "MedForge-public-smoke/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        tcia_bytes = response.read()
    loaded = med_io.load_dicom_bytes(tcia_bytes, "TCIA_getSingleImage.dcm")
    results.append(
        exercise_pipeline(
            "TCIA public single DICOM",
            loaded,
            "The Cancer Imaging Archive public getSingleImage example endpoint",
        )
    )

    report = {
        "suite": "MedForge public imaging smoke test",
        "result_count": len(results),
        "passed": sum(1 for x in results if x["status"] == "PASS"),
        "failed": sum(1 for x in results if x["status"] != "PASS"),
        "results": results,
        "known_scope_limits": [
            "Initial prototype tests single rendered medical images, not complete DICOM series.",
            "No automated diagnosis or pathology classification is performed.",
            "Mechanism steps are software-test hypotheses and are not clinical conclusions.",
        ],
    }
    print(json.dumps(report, indent=2))
    (ROOT / "medforge-public-smoke-report.json").write_text(json.dumps(report, indent=2))
    if report["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
