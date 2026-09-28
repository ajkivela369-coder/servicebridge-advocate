from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import zipfile

import numpy as np

REPO = Path(__file__).resolve().parents[1]
MED = REPO / "apps" / "medforge-imaging-studio"
import sys
if str(MED) not in sys.path:
    sys.path.insert(0, str(MED))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from med_mesh import MeshData
from med_motion import motion_from_dict
from med_native3d import NativeRenderSettings, render_native_animation


def load_obj(path: Path, *, name: str, provenance: str) -> MeshData:
    vertices = []
    faces = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            parts = line.split()[1:4]
            faces.append(tuple(int(x.split("/")[0]) - 1 for x in parts))
    return MeshData(
        name=name,
        vertices_ras_mm=np.asarray(vertices, dtype=np.float32),
        faces=np.asarray(faces, dtype=np.int32),
        source_voxels=0,
        provenance=provenance,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Render a MedForge 3D scene bundle without Blender."
    )
    parser.add_argument("bundle")
    parser.add_argument("--output", default="./medforge-native3d.mp4")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    with tempfile.TemporaryDirectory(prefix="medforge-native-bundle-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(bundle) as zf:
            zf.extractall(root)
        spec = json.loads((root / "scene.json").read_text())

        meshes = []
        for item in spec.get("objects", []):
            meshes.append((
                item["object_id"],
                load_obj(
                    root / item["obj_path"],
                    name=item.get("name", item["object_id"]),
                    provenance=item.get("provenance", "bundle mesh"),
                ),
            ))
        motions = [motion_from_dict(x) for x in spec.get("motions", [])]
        settings = NativeRenderSettings(
            fps=int(spec.get("fps", 30)),
            frame_start=int(spec.get("frame_start", 1)),
            frame_end=int(spec.get("frame_end", 90)),
            width=int(spec.get("width", 1280)),
            height=int(spec.get("height", 720)),
        )
        output = render_native_animation(
            meshes,
            motions,
            args.output,
            settings=settings,
        )
    print(f"Rendered: {output}")


if __name__ == "__main__":
    main()
