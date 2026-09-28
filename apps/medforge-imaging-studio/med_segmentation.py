from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import numpy as np


SEGMENTATION_ENGINES: Dict[str, dict] = {
    "Intensity exploration": {
        "status": "connected",
        "role": "Create a simple threshold mask for visualization/testing only.",
        "clinical_meaning": "none",
    },
    "TotalSegmentator": {
        "status": "planned",
        "role": "Anatomy segmentation for CT/MR through a local or GPU worker.",
        "clinical_meaning": "anatomical segmentation aid; not diagnosis",
    },
    "MONAI Label": {
        "status": "planned",
        "role": "Interactive AI-assisted annotation and label correction.",
        "clinical_meaning": "annotation aid; labels require review",
    },
}


@dataclass
class SegmentationSummary:
    method: str
    voxel_count: int
    fraction_of_volume: float
    note: str

    def to_dict(self):
        return asdict(self)


def percentile_mask(volume: np.ndarray, percentile: float = 85.0) -> np.ndarray:
    """
    Return a boolean high-intensity mask for UI/volume-pipeline testing.

    This is deliberately not called anatomy segmentation. It has no diagnostic
    or anatomical meaning; it simply proves that masks can flow through the
    same viewer and renderer contracts.
    """
    v = np.asarray(volume, dtype=np.float32)
    finite = v[np.isfinite(v)]
    if finite.size == 0:
        raise ValueError("Volume has no finite voxels.")
    p = float(np.clip(percentile, 0.0, 100.0))
    threshold = float(np.percentile(finite, p))
    return np.isfinite(v) & (v >= threshold)


def summarize_mask(mask: np.ndarray, method: str = "Intensity exploration") -> SegmentationSummary:
    m = np.asarray(mask, dtype=bool)
    total = int(m.size)
    count = int(m.sum())
    return SegmentationSummary(
        method=method,
        voxel_count=count,
        fraction_of_volume=(count / total) if total else 0.0,
        note="Exploratory software-test mask; not an anatomical or diagnostic segmentation.",
    )


def totalsegmentator_job_spec(task: str = "total") -> dict:
    """
    Provider-neutral job contract for a future TotalSegmentator worker.
    No external command is executed by this function.
    """
    return {
        "engine": "TotalSegmentator",
        "status": "planned",
        "task": task,
        "input_contract": "de-identified DICOM series or NIfTI volume",
        "output_contract": "one mask per requested anatomical class plus provenance metadata",
        "review_required": True,
        "diagnosis_claim": False,
    }


def monai_label_job_spec() -> dict:
    return {
        "engine": "MONAI Label",
        "status": "planned",
        "input_contract": "de-identified image volume plus optional seed labels",
        "output_contract": "editable segmentation labels with model/application provenance",
        "review_required": True,
        "diagnosis_claim": False,
    }
