from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class AlignmentReport:
    source_shape: tuple[int, int, int]
    mask_shape: tuple[int, int, int]
    source_spacing_mm: tuple[float, float, float]
    mask_spacing_mm: tuple[float, float, float]
    source_center_ras_mm: tuple[float, float, float]
    mask_center_ras_mm: tuple[float, float, float]
    center_distance_mm: float
    physical_overlap_ratio: float
    source_affine_valid: bool
    mask_affine_valid: bool
    spatial_overlay_ready: bool
    reason: str

    def to_dict(self):
        return asdict(self)


def _valid_affine(affine) -> bool:
    try:
        a = np.asarray(affine, dtype=np.float64)
        return (
            a.shape == (4, 4)
            and bool(np.isfinite(a).all())
            and abs(float(np.linalg.det(a[:3, :3]))) > 1e-9
        )
    except Exception:
        return False


def voxel_spacing_mm(affine) -> tuple[float, float, float]:
    a = np.asarray(affine, dtype=np.float64)
    return tuple(float(np.linalg.norm(a[:3, i])) for i in range(3))


def world_corners(shape: Iterable[int], affine) -> np.ndarray:
    shape = tuple(int(x) for x in shape)
    if len(shape) != 3:
        raise ValueError("Expected a 3D shape.")
    a = np.asarray(affine, dtype=np.float64)
    if not _valid_affine(a):
        raise ValueError("Affine is missing, non-finite, or singular.")

    maxima = [max(0, x - 1) for x in shape]
    corners = []
    for i in (0, maxima[0]):
        for j in (0, maxima[1]):
            for k in (0, maxima[2]):
                world = a @ np.asarray([i, j, k, 1.0], dtype=np.float64)
                corners.append(world[:3])
    return np.asarray(corners, dtype=np.float64)


def _bounds(corners: np.ndarray):
    return corners.min(axis=0), corners.max(axis=0)


def _bbox_overlap_ratio(a_corners: np.ndarray, b_corners: np.ndarray) -> float:
    a_min, a_max = _bounds(a_corners)
    b_min, b_max = _bounds(b_corners)
    lo = np.maximum(a_min, b_min)
    hi = np.minimum(a_max, b_max)
    intersection = np.maximum(0.0, hi - lo)
    intersection_volume = float(np.prod(intersection))

    a_volume = float(np.prod(np.maximum(1e-6, a_max - a_min)))
    b_volume = float(np.prod(np.maximum(1e-6, b_max - b_min)))
    denominator = max(1e-6, min(a_volume, b_volume))
    return float(np.clip(intersection_volume / denominator, 0.0, 1.0))


def _center(shape, affine) -> np.ndarray:
    index = np.asarray([(int(s) - 1) / 2.0 for s in shape] + [1.0], dtype=np.float64)
    return (np.asarray(affine, dtype=np.float64) @ index)[:3]


def alignment_report(
    source_shape,
    source_affine_zyx_ras,
    mask_shape,
    mask_affine_ras,
    *,
    minimum_overlap_ratio: float = 0.70,
) -> AlignmentReport:
    source_shape = tuple(int(x) for x in source_shape)
    mask_shape = tuple(int(x) for x in mask_shape)
    source_valid = _valid_affine(source_affine_zyx_ras)
    mask_valid = _valid_affine(mask_affine_ras)

    if not source_valid or not mask_valid:
        return AlignmentReport(
            source_shape=source_shape,
            mask_shape=mask_shape,
            source_spacing_mm=(0.0, 0.0, 0.0),
            mask_spacing_mm=(0.0, 0.0, 0.0),
            source_center_ras_mm=(0.0, 0.0, 0.0),
            mask_center_ras_mm=(0.0, 0.0, 0.0),
            center_distance_mm=float("inf"),
            physical_overlap_ratio=0.0,
            source_affine_valid=source_valid,
            mask_affine_valid=mask_valid,
            spatial_overlay_ready=False,
            reason="Both DICOM and NIfTI require finite, invertible patient-space affines before overlay.",
        )

    source_corners = world_corners(source_shape, source_affine_zyx_ras)
    mask_corners = world_corners(mask_shape, mask_affine_ras)
    overlap = _bbox_overlap_ratio(source_corners, mask_corners)
    source_center = _center(source_shape, source_affine_zyx_ras)
    mask_center = _center(mask_shape, mask_affine_ras)
    center_distance = float(np.linalg.norm(source_center - mask_center))
    ready = overlap >= float(minimum_overlap_ratio)

    reason = (
        "Patient-space geometry overlaps sufficiently for nearest-neighbor resampling into the DICOM grid."
        if ready
        else
        "Patient-space overlap is too small for a trustworthy automatic overlay; inspect the source/mask pairing."
    )

    return AlignmentReport(
        source_shape=source_shape,
        mask_shape=mask_shape,
        source_spacing_mm=voxel_spacing_mm(source_affine_zyx_ras),
        mask_spacing_mm=voxel_spacing_mm(mask_affine_ras),
        source_center_ras_mm=tuple(float(x) for x in source_center),
        mask_center_ras_mm=tuple(float(x) for x in mask_center),
        center_distance_mm=center_distance,
        physical_overlap_ratio=overlap,
        source_affine_valid=True,
        mask_affine_valid=True,
        spatial_overlay_ready=ready,
        reason=reason,
    )


def resample_mask_to_source(
    mask_data: np.ndarray,
    mask_affine_ras,
    source_shape,
    source_affine_zyx_ras,
    *,
    minimum_overlap_ratio: float = 0.70,
) -> tuple[np.ndarray, AlignmentReport]:
    report = alignment_report(
        source_shape,
        source_affine_zyx_ras,
        mask_data.shape,
        mask_affine_ras,
        minimum_overlap_ratio=minimum_overlap_ratio,
    )
    if not report.spatial_overlay_ready:
        raise ValueError(report.reason)

    try:
        from scipy.ndimage import affine_transform
    except ImportError as exc:
        raise RuntimeError(
            "Spatial mask resampling requires scipy. Install the MedForge requirements."
        ) from exc

    source_affine = np.asarray(source_affine_zyx_ras, dtype=np.float64)
    mask_affine = np.asarray(mask_affine_ras, dtype=np.float64)
    source_to_mask = np.linalg.inv(mask_affine) @ source_affine

    aligned = affine_transform(
        np.asarray(mask_data, dtype=np.uint8),
        matrix=source_to_mask[:3, :3],
        offset=source_to_mask[:3, 3],
        output_shape=tuple(int(x) for x in source_shape),
        order=0,
        mode="constant",
        cval=0,
        prefilter=False,
    )
    return np.asarray(aligned > 0, dtype=bool), report


def affine_round_trip_error_mm(affine, points: np.ndarray) -> float:
    """Numerical sanity check for voxel->world->voxel transforms."""
    a = np.asarray(affine, dtype=np.float64)
    if not _valid_affine(a):
        return float("inf")
    inv = np.linalg.inv(a)
    p = np.asarray(points, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("points must be an N x 3 array.")
    hom = np.concatenate([p, np.ones((len(p), 1))], axis=1)
    world = (a @ hom.T).T
    restored = (inv @ world.T).T[:, :3]
    return float(np.max(np.linalg.norm(restored - p, axis=1))) if len(p) else 0.0
