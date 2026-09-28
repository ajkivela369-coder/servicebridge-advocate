from __future__ import annotations

from dataclasses import dataclass, asdict
from io import StringIO

import numpy as np


@dataclass(frozen=True)
class MeshData:
    name: str
    vertices_ras_mm: np.ndarray
    faces: np.ndarray
    source_voxels: int
    provenance: str
    evidence_class: str = "DERIVED / UNREVIEWED"

    def summary(self) -> dict:
        vertices = np.asarray(self.vertices_ras_mm, dtype=np.float64)
        return {
            "name": self.name,
            "vertices": int(len(vertices)),
            "faces": int(len(self.faces)),
            "source_voxels": int(self.source_voxels),
            "provenance": self.provenance,
            "evidence_class": self.evidence_class,
            "bounds_ras_mm": {
                "min": [float(x) for x in vertices.min(axis=0)] if len(vertices) else [0.0, 0.0, 0.0],
                "max": [float(x) for x in vertices.max(axis=0)] if len(vertices) else [0.0, 0.0, 0.0],
            },
        }


def mask_to_mesh(mask, affine_ras, *, name: str, provenance: str, step_size: int = 1) -> MeshData:
    """
    Convert a binary NIfTI mask into a surface mesh in patient RAS millimeters.

    This is a geometric reconstruction of a DERIVED mask. It does not upgrade
    the mask's anatomical/clinical validity.
    """
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 3:
        raise ValueError("Expected a 3D mask.")
    if not m.any():
        raise ValueError("Cannot mesh an empty mask.")
    affine = np.asarray(affine_ras, dtype=np.float64)
    if affine.shape != (4, 4) or not np.isfinite(affine).all():
        raise ValueError("A finite 4x4 NIfTI affine is required.")
    if abs(float(np.linalg.det(affine[:3, :3]))) <= 1e-9:
        raise ValueError("NIfTI affine must be invertible; singular geometry cannot be meshed safely.")

    try:
        from skimage.measure import marching_cubes
    except ImportError as exc:
        raise RuntimeError("Mask meshing requires scikit-image.") from exc

    # Padding guarantees a closed outside boundary even when the mask touches
    # the array edge. Subtract one voxel from returned coordinates afterward.
    padded = np.pad(m.astype(np.float32), 1, mode="constant", constant_values=0)
    vertices, faces, _normals, _values = marching_cubes(
        padded,
        level=0.5,
        step_size=max(1, int(step_size)),
        allow_degenerate=False,
    )
    vertices = vertices - 1.0
    hom = np.concatenate(
        [vertices.astype(np.float64), np.ones((len(vertices), 1), dtype=np.float64)],
        axis=1,
    )
    world = (affine @ hom.T).T[:, :3]

    return MeshData(
        name=name,
        vertices_ras_mm=np.asarray(world, dtype=np.float32),
        faces=np.asarray(faces, dtype=np.int32),
        source_voxels=int(m.sum()),
        provenance=provenance,
    )


def mesh_to_obj(mesh: MeshData) -> bytes:
    """Serialize one mesh as a plain Wavefront OBJ in RAS millimeters."""
    out = StringIO()
    out.write(f"# MedForge derived mesh: {mesh.name}\n")
    out.write(f"# Evidence class: {mesh.evidence_class}\n")
    out.write(f"# Provenance: {mesh.provenance}\n")
    for x, y, z in np.asarray(mesh.vertices_ras_mm):
        out.write(f"v {float(x):.6f} {float(y):.6f} {float(z):.6f}\n")
    for a, b, c in np.asarray(mesh.faces):
        # OBJ indices are 1-based.
        out.write(f"f {int(a)+1} {int(b)+1} {int(c)+1}\n")
    return out.getvalue().encode("utf-8")


def mesh_surface_area_mm2(mesh: MeshData) -> float:
    v = np.asarray(mesh.vertices_ras_mm, dtype=np.float64)
    f = np.asarray(mesh.faces, dtype=np.int64)
    if not len(f):
        return 0.0
    a = v[f[:, 0]]
    b = v[f[:, 1]]
    c = v[f[:, 2]]
    cross = np.cross(b - a, c - a)
    return float(0.5 * np.linalg.norm(cross, axis=1).sum())
