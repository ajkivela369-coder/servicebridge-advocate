from __future__ import annotations

from dataclasses import dataclass, asdict
from io import BytesIO
from typing import Iterable, List, Tuple
import math

import numpy as np
from PIL import Image

try:
    import pydicom
except Exception:
    pydicom = None


@dataclass
class DicomSeriesInfo:
    series_uid: str
    modality: str
    description: str
    instance_count: int
    rows: int
    columns: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VolumeStudy:
    volume: np.ndarray
    modality: str
    description: str
    series_uid: str
    spacing_zyx: Tuple[float, float, float]
    source_files_count: int
    decode_warnings: List[str]

    @property
    def shape(self):
        return tuple(int(x) for x in self.volume.shape)

    def safe_summary(self) -> dict:
        return {
            "modality": self.modality,
            "description": self.description,
            "series_uid_present": bool(self.series_uid),
            "shape_zyx": list(self.shape),
            "spacing_zyx": [float(x) for x in self.spacing_zyx],
            "source_files_count": int(self.source_files_count),
            "decode_warnings": list(self.decode_warnings),
            "raw_dicom_headers_retained": False,
        }


def _require_pydicom():
    if pydicom is None:
        raise RuntimeError("pydicom is required for DICOM-series support.")


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _series_uid(ds) -> str:
    return str(getattr(ds, "SeriesInstanceUID", "") or "NO_SERIES_UID")


def _slice_sort_value(ds, fallback_index: int):
    # Prefer true geometric position along the slice normal.
    try:
        iop = np.asarray([float(v) for v in ds.ImageOrientationPatient], dtype=np.float64)
        ipp = np.asarray([float(v) for v in ds.ImagePositionPatient], dtype=np.float64)
        if iop.shape == (6,) and ipp.shape == (3,):
            row = iop[:3]
            col = iop[3:]
            normal = np.cross(row, col)
            norm = float(np.linalg.norm(normal))
            if norm > 0:
                normal = normal / norm
                return 0, float(np.dot(ipp, normal))
    except Exception:
        pass

    slice_location = _safe_float(getattr(ds, "SliceLocation", None))
    if slice_location is not None:
        return 1, slice_location

    instance = _safe_int(getattr(ds, "InstanceNumber", None), fallback_index)
    return 2, float(instance)


def inspect_dicom_series(files: Iterable[Tuple[str, bytes]]) -> List[DicomSeriesInfo]:
    """Return PHI-minimized series summaries without decoding pixel arrays."""
    _require_pydicom()
    grouped = {}
    for name, raw in files:
        try:
            ds = pydicom.dcmread(BytesIO(raw), stop_before_pixels=True, force=True)
        except Exception:
            continue
        uid = _series_uid(ds)
        entry = grouped.setdefault(
            uid,
            {
                "series_uid": uid,
                "modality": str(getattr(ds, "Modality", "") or "DICOM"),
                "description": str(getattr(ds, "SeriesDescription", "") or ""),
                "instance_count": 0,
                "rows": _safe_int(getattr(ds, "Rows", 0)),
                "columns": _safe_int(getattr(ds, "Columns", 0)),
            },
        )
        entry["instance_count"] += 1

    infos = [DicomSeriesInfo(**x) for x in grouped.values()]
    infos.sort(key=lambda x: (-x.instance_count, x.modality, x.description))
    return infos


def _decode_frame(ds, warnings: List[str], source_name: str) -> np.ndarray:
    try:
        arr = np.asarray(ds.pixel_array)
    except Exception as exc:
        warnings.append(f"{source_name}: pixel decode failed: {type(exc).__name__}: {exc}")
        raise

    # RGB/color DICOM is not suitable for volume assembly in this prototype.
    if arr.ndim == 3 and arr.shape[-1] in (3, 4):
        raise ValueError(f"{source_name}: color DICOM is not supported for 3D volume assembly.")

    slope = _safe_float(getattr(ds, "RescaleSlope", 1), 1.0) or 1.0
    intercept = _safe_float(getattr(ds, "RescaleIntercept", 0), 0.0) or 0.0
    arr = arr.astype(np.float32) * float(slope) + float(intercept)

    if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        finite = arr[np.isfinite(arr)]
        if finite.size:
            arr = float(finite.max() + finite.min()) - arr

    return arr


def _slice_spacing(sorted_datasets) -> float:
    positions = []
    for index, (_, ds) in enumerate(sorted_datasets):
        mode, value = _slice_sort_value(ds, index)
        if mode == 0:
            positions.append(value)
    if len(positions) >= 2:
        diffs = np.diff(np.asarray(positions, dtype=np.float64))
        diffs = np.abs(diffs[np.abs(diffs) > 1e-6])
        if diffs.size:
            return float(np.median(diffs))

    for _, ds in sorted_datasets:
        for attr in ("SpacingBetweenSlices", "SliceThickness"):
            v = _safe_float(getattr(ds, attr, None))
            if v is not None and v > 0:
                return float(v)
    return 1.0


def build_dicom_volume(
    files: Iterable[Tuple[str, bytes]],
    series_uid: str | None = None,
) -> VolumeStudy:
    """
    Assemble one grayscale DICOM series into a z,y,x float32 volume.

    This returns pixel data and PHI-minimized geometry only. The raw pydicom
    Dataset objects are deliberately not retained.
    """
    _require_pydicom()
    parsed = []
    warnings: List[str] = []

    for index, (name, raw) in enumerate(files):
        try:
            ds = pydicom.dcmread(BytesIO(raw), force=True)
        except Exception as exc:
            warnings.append(f"{name}: DICOM read failed: {type(exc).__name__}: {exc}")
            continue
        if "PixelData" not in ds:
            warnings.append(f"{name}: no PixelData; skipped.")
            continue
        if series_uid is not None and _series_uid(ds) != series_uid:
            continue
        parsed.append((name, ds))

    if not parsed:
        raise ValueError("No pixel-bearing DICOM instances matched the selected series.")

    if series_uid is None:
        counts = {}
        for _, ds in parsed:
            uid = _series_uid(ds)
            counts[uid] = counts.get(uid, 0) + 1
        chosen_uid = max(counts.items(), key=lambda kv: kv[1])[0]
        parsed = [(n, ds) for n, ds in parsed if _series_uid(ds) == chosen_uid]
        series_uid = chosen_uid

    indexed = list(enumerate(parsed))
    indexed.sort(key=lambda pair: _slice_sort_value(pair[1][1], pair[0]))
    parsed = [item for _, item in indexed]

    decoded_slices = []
    expected_shape = None
    for name, ds in parsed:
        arr = _decode_frame(ds, warnings, name)

        if arr.ndim == 2:
            frames = [arr]
        elif arr.ndim == 3:
            frames = [arr[i] for i in range(arr.shape[0])]
        else:
            warnings.append(f"{name}: unsupported pixel shape {arr.shape}; skipped.")
            continue

        for frame in frames:
            if expected_shape is None:
                expected_shape = tuple(frame.shape)
            if tuple(frame.shape) != expected_shape:
                warnings.append(
                    f"{name}: frame shape {tuple(frame.shape)} does not match {expected_shape}; skipped."
                )
                continue
            decoded_slices.append(frame.astype(np.float32, copy=False))

    if not decoded_slices:
        raise ValueError("DICOM files were readable but no compatible grayscale frames could be assembled.")

    volume = np.stack(decoded_slices, axis=0).astype(np.float32, copy=False)
    first = parsed[0][1]
    pixel_spacing = getattr(first, "PixelSpacing", None)
    try:
        row_spacing = float(pixel_spacing[0])
        col_spacing = float(pixel_spacing[1])
    except Exception:
        row_spacing = col_spacing = 1.0
    z_spacing = _slice_spacing(parsed)

    return VolumeStudy(
        volume=volume,
        modality=str(getattr(first, "Modality", "") or "DICOM"),
        description=str(getattr(first, "SeriesDescription", "") or ""),
        series_uid=str(series_uid or ""),
        spacing_zyx=(float(z_spacing), float(row_spacing), float(col_spacing)),
        source_files_count=len(parsed),
        decode_warnings=warnings,
    )


def mpr_slices(volume: np.ndarray, z: int, y: int, x: int):
    """Return axial, coronal and sagittal planes from a z,y,x volume."""
    if volume.ndim != 3:
        raise ValueError(f"Expected 3D volume, got shape {volume.shape}.")
    z = int(np.clip(z, 0, volume.shape[0] - 1))
    y = int(np.clip(y, 0, volume.shape[1] - 1))
    x = int(np.clip(x, 0, volume.shape[2] - 1))

    axial = volume[z, :, :]
    coronal = np.flipud(volume[:, y, :])
    sagittal = np.flipud(volume[:, :, x])
    return axial, coronal, sagittal


def window_to_pil(arr: np.ndarray, low: float | None = None, high: float | None = None) -> Image.Image:
    """Convert one numeric medical-image plane to display RGB without altering source data."""
    a = np.asarray(arr, dtype=np.float32)
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        raise ValueError("Image plane has no finite pixels.")

    if low is None or high is None or high <= low:
        low, high = np.percentile(finite, (1, 99))
        low = float(low)
        high = float(high)
    if high <= low:
        high = low + 1.0

    scaled = np.clip((np.nan_to_num(a, nan=low) - low) / (high - low), 0, 1)
    return Image.fromarray((scaled * 255).astype(np.uint8)).convert("RGB")


def downsample_volume(volume: np.ndarray, max_axis: int = 48) -> np.ndarray:
    """Cheap deterministic downsampling for browser 3D previews."""
    if volume.ndim != 3:
        raise ValueError("Expected a 3D volume.")
    steps = [max(1, math.ceil(size / max_axis)) for size in volume.shape]
    return volume[::steps[0], ::steps[1], ::steps[2]]
