from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from med_mesh import MeshData
from med_motion import MechanismMotion
from med_native3d import transform_vertices


@dataclass(frozen=True)
class ProximitySample:
    frame: int
    distance_mm: float
    point_a_ras_mm: tuple[float, float, float]
    point_b_ras_mm: tuple[float, float, float]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ProximitySeries:
    object_a: str
    object_b: str
    samples: tuple[ProximitySample, ...]
    minimum_distance_mm: float
    minimum_frame: int
    interpretation: str = (
        "Geometric surface-to-surface proximity only. This does not measure tissue force, "
        "vascular flow, nerve irritation, deformation, pathology, or causation."
    )

    def to_dict(self):
        return {
            "object_a": self.object_a,
            "object_b": self.object_b,
            "samples": [x.to_dict() for x in self.samples],
            "minimum_distance_mm": float(self.minimum_distance_mm),
            "minimum_frame": int(self.minimum_frame),
            "interpretation": self.interpretation,
        }


def nearest_surface_distance(
    vertices_a: np.ndarray,
    vertices_b: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    a = np.asarray(vertices_a, dtype=np.float64)
    b = np.asarray(vertices_b, dtype=np.float64)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1:] != (3,) or b.shape[1:] != (3,):
        raise ValueError("Both vertex arrays must be N x 3.")
    if len(a) == 0 or len(b) == 0:
        raise ValueError("Both meshes require at least one vertex.")

    try:
        from scipy.spatial import cKDTree
    except ImportError as exc:
        raise RuntimeError("Proximity measurement requires scipy.") from exc

    # Query the smaller set against a tree of the larger set to reduce work.
    if len(a) <= len(b):
        tree = cKDTree(b)
        distances, indices = tree.query(a, k=1)
        idx_a = int(np.argmin(distances))
        idx_b = int(indices[idx_a])
    else:
        tree = cKDTree(a)
        distances, indices = tree.query(b, k=1)
        idx_b = int(np.argmin(distances))
        idx_a = int(indices[idx_b])

    point_a = a[idx_a]
    point_b = b[idx_b]
    distance = float(np.linalg.norm(point_a - point_b))
    return distance, point_a, point_b


def proximity_over_motion(
    object_a: str,
    mesh_a: MeshData,
    object_b: str,
    mesh_b: MeshData,
    *,
    motion_a: MechanismMotion | None = None,
    motion_b: MechanismMotion | None = None,
    frames: Iterable[int],
) -> ProximitySeries:
    if object_a == object_b:
        raise ValueError("Choose two different structures for proximity measurement.")

    samples = []
    for frame in [int(x) for x in frames]:
        va = transform_vertices(mesh_a.vertices_ras_mm, motion_a, frame)
        vb = transform_vertices(mesh_b.vertices_ras_mm, motion_b, frame)
        distance, pa, pb = nearest_surface_distance(va, vb)
        samples.append(
            ProximitySample(
                frame=frame,
                distance_mm=distance,
                point_a_ras_mm=tuple(float(x) for x in pa),
                point_b_ras_mm=tuple(float(x) for x in pb),
            )
        )

    if not samples:
        raise ValueError("At least one frame is required.")

    minimum = min(samples, key=lambda x: x.distance_mm)
    return ProximitySeries(
        object_a=object_a,
        object_b=object_b,
        samples=tuple(samples),
        minimum_distance_mm=minimum.distance_mm,
        minimum_frame=minimum.frame,
    )
