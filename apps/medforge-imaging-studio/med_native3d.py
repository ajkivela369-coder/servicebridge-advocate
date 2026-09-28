from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import shutil
import tempfile
from typing import Iterable

import numpy as np

from med_mesh import MeshData
from med_motion import MechanismMotion


@dataclass(frozen=True)
class NativeRenderSettings:
    fps: int = 30
    frame_start: int = 1
    frame_end: int = 90
    width: int = 1280
    height: int = 720
    dpi: int = 100
    elevation_deg: float = 18.0
    azimuth_deg: float = -62.0


def rotation_matrix_xyz(degrees_xyz) -> np.ndarray:
    rx, ry, rz = [math.radians(float(x)) for x in degrees_xyz]
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    mx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]], dtype=np.float64)
    my = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]], dtype=np.float64)
    mz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]], dtype=np.float64)
    return mz @ my @ mx


def motion_fraction(motion: MechanismMotion, frame: int) -> float:
    if frame <= motion.start_frame:
        return 0.0
    if frame >= motion.end_frame:
        return 1.0
    return float(frame - motion.start_frame) / float(motion.end_frame - motion.start_frame)


def transform_vertices(
    vertices: np.ndarray,
    motion: MechanismMotion | None,
    frame: int,
) -> np.ndarray:
    v = np.asarray(vertices, dtype=np.float64)
    if motion is None or len(v) == 0:
        return v.copy()

    t = motion_fraction(motion, int(frame))
    rotation = rotation_matrix_xyz(
        tuple(float(x) * t for x in motion.rotation_deg_xyz)
    )
    translation = np.asarray(
        [float(x) * t for x in motion.translation_mm_xyz],
        dtype=np.float64,
    )

    center = v.mean(axis=0)
    transformed = (rotation @ (v - center).T).T + center + translation
    return transformed


def scene_bounds(meshes: Iterable[MeshData]) -> tuple[np.ndarray, np.ndarray]:
    arrays = [np.asarray(m.vertices_ras_mm, dtype=np.float64) for m in meshes if len(m.vertices_ras_mm)]
    if not arrays:
        raise ValueError("No mesh vertices are available.")
    all_vertices = np.concatenate(arrays, axis=0)
    return all_vertices.min(axis=0), all_vertices.max(axis=0)


def render_native_frame(
    meshes: list[tuple[str, MeshData]],
    motions: dict[str, MechanismMotion],
    frame: int,
    output_png: str | Path,
    *,
    settings: NativeRenderSettings,
) -> Path:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError as exc:
        raise RuntimeError("Native 3D rendering requires matplotlib.") from exc

    output = Path(output_png)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(
        figsize=(settings.width / settings.dpi, settings.height / settings.dpi),
        dpi=settings.dpi,
    )
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor((0.03, 0.04, 0.045))
    fig.patch.set_facecolor((0.03, 0.04, 0.045))

    palette = [
        (0.25, 0.65, 0.75),
        (0.78, 0.50, 0.20),
        (0.40, 0.72, 0.43),
        (0.64, 0.43, 0.73),
        (0.78, 0.32, 0.30),
    ]

    transformed_meshes = []
    for index, (object_id, mesh) in enumerate(meshes):
        vertices = transform_vertices(
            mesh.vertices_ras_mm,
            motions.get(object_id),
            frame,
        )
        faces = np.asarray(mesh.faces, dtype=np.int64)
        transformed_meshes.append(vertices)
        poly = Poly3DCollection(
            vertices[faces],
            alpha=0.78,
            linewidths=0.08,
        )
        poly.set_facecolor(palette[index % len(palette)])
        poly.set_edgecolor((0.88, 0.92, 0.93, 0.18))
        ax.add_collection3d(poly)

    all_vertices = np.concatenate(transformed_meshes, axis=0)
    mn = all_vertices.min(axis=0)
    mx = all_vertices.max(axis=0)
    center = (mn + mx) / 2.0
    span = max(float(np.max(mx - mn)), 1.0) * 0.62
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span, center[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=settings.elevation_deg, azim=settings.azimuth_deg)
    ax.set_axis_off()

    fig.text(
        0.02,
        0.97,
        "ILLUSTRATIVE / DERIVED",
        ha="left",
        va="top",
        fontsize=11,
        color="white",
        weight="bold",
    )
    fig.text(
        0.02,
        0.025,
        "Segmentation-derived geometry · motion is user/record-specified · not proof of diagnosis or causation",
        ha="left",
        va="bottom",
        fontsize=7.5,
        color=(0.8, 0.84, 0.85),
    )
    fig.savefig(output, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return output


def render_native_animation(
    meshes: list[tuple[str, MeshData]],
    motions: Iterable[MechanismMotion],
    output_mp4: str | Path,
    *,
    settings: NativeRenderSettings | None = None,
) -> Path:
    settings = settings or NativeRenderSettings()
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for the native MedForge 3D renderer.")

    motion_map = {m.structure_id: m for m in motions}
    output = Path(output_mp4)
    output.parent.mkdir(parents=True, exist_ok=True)

    from servicebridge.local_runtime.media import image_sequence_command, run_command

    with tempfile.TemporaryDirectory(prefix="medforge-native3d-") as tmp:
        tmp_path = Path(tmp)
        for frame in range(settings.frame_start, settings.frame_end + 1):
            render_native_frame(
                meshes,
                motion_map,
                frame,
                tmp_path / f"frame_{frame:04d}.png",
                settings=settings,
            )

        command = image_sequence_command(
            str(tmp_path / "frame_%04d.png"),
            output,
            fps=settings.fps,
            width=settings.width,
            height=settings.height,
        )
        # image_sequence_command starts at frame 0 by default; tell ffmpeg our
        # generated numbering starts at frame_start.
        command[4:4] = ["-start_number", str(settings.frame_start)]
        run_command(command, timeout=max(600.0, (settings.frame_end - settings.frame_start + 1) * 15.0))

    return output
