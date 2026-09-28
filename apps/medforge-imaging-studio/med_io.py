from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

try:
    import pydicom
except Exception:
    pydicom = None


@dataclass
class LoadedMedicalImage:
    image: Image.Image
    source_name: str
    source_kind: str
    modality: str
    width: int
    height: int
    raw_dicom_headers_retained: bool = False


def normalize_array_to_rgb(arr: np.ndarray, *, window_center=None, window_width=None) -> Image.Image:
    arr = np.asarray(arr, dtype=np.float32)

    if window_center is not None and window_width is not None:
        try:
            center = float(window_center[0] if hasattr(window_center, "__len__") and not isinstance(window_center, str) else window_center)
            width = float(window_width[0] if hasattr(window_width, "__len__") and not isinstance(window_width, str) else window_width)
            if width > 0:
                arr = np.clip(arr, center - width / 2, center + width / 2)
        except Exception:
            pass

    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        raise ValueError("Image has no finite pixel values.")

    lo, hi = np.percentile(finite, (1, 99))
    if hi <= lo:
        lo, hi = float(finite.min()), float(finite.max())
    if hi <= lo:
        hi = lo + 1.0

    arr = np.nan_to_num(arr, nan=lo, posinf=hi, neginf=lo)
    arr = np.clip((arr - lo) / (hi - lo), 0, 1)
    return Image.fromarray((arr * 255).astype(np.uint8)).convert("RGB")


def load_standard_image_bytes(raw: bytes, source_name: str = "image") -> LoadedMedicalImage:
    if not raw:
        raise ValueError("Image file is empty.")
    img = Image.open(io.BytesIO(raw))
    img.load()
    img = img.convert("RGB")
    return LoadedMedicalImage(
        image=img,
        source_name=source_name,
        source_kind="standard-image",
        modality="Unknown / image",
        width=img.width,
        height=img.height,
        raw_dicom_headers_retained=False,
    )


def load_dicom_bytes(raw: bytes, source_name: str = "image.dcm") -> LoadedMedicalImage:
    if pydicom is None:
        raise RuntimeError("pydicom is required for DICOM support.")
    if not raw:
        raise ValueError("DICOM file is empty.")

    ds = pydicom.dcmread(io.BytesIO(raw), force=True)
    if "PixelData" not in ds:
        raise ValueError("DICOM object does not contain pixel data.")

    arr = ds.pixel_array.astype(np.float32)
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
    arr = arr * slope + intercept

    # Initial MedForge supports a single rendered image. If the source is
    # multi-frame, use a deterministic middle frame for preview and report it.
    if arr.ndim >= 3 and arr.shape[-1] not in (3, 4):
        arr = arr[arr.shape[0] // 2]

    img = normalize_array_to_rgb(
        arr,
        window_center=getattr(ds, "WindowCenter", None),
        window_width=getattr(ds, "WindowWidth", None),
    )
    modality = str(getattr(ds, "Modality", "") or "DICOM")
    return LoadedMedicalImage(
        image=img,
        source_name=source_name,
        source_kind="dicom",
        modality=modality,
        width=img.width,
        height=img.height,
        # We intentionally return rendered pixels + minimal modality only.
        # The caller never receives the raw Dataset for project export.
        raw_dicom_headers_retained=False,
    )


def load_medical_image_bytes(raw: bytes, source_name: str) -> LoadedMedicalImage:
    suffix = Path(source_name).suffix.lower()
    if suffix == ".dcm":
        return load_dicom_bytes(raw, source_name)
    return load_standard_image_bytes(raw, source_name)
