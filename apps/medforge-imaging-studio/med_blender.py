from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from med_mesh import mask_to_mesh, mesh_surface_area_mm2, mesh_to_obj
from med_motion import MechanismMotion, motion_manifest


def safe_object_id(name: str) -> str:
    stem = name
    for suffix in (".nii.gz", ".nii", ".obj"):
        if stem.lower().endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")
    return cleaned or "structure"


def build_blender_scene_bundle(
    masks,
    motions: list[MechanismMotion] | None = None,
    *,
    title: str = "MedForge Illustrative Mechanism",
    fps: int = 30,
    frame_end: int = 90,
    width: int = 1280,
    height: int = 720,
    mesh_step_size: int = 1,
    render_video: bool = False,
) -> bytes:
    """
    Build a self-contained Blender handoff ZIP.

    The ZIP contains derived OBJ meshes, patient-space geometry metadata,
    explicit illustrative motions, the Blender scene script, and evidence rules.
    Raw DICOM is never included.
    """
    masks = list(masks)
    if not masks:
        raise ValueError("At least one imported segmentation mask is required.")
    motions = list(motions or [])

    objects = []
    mesh_files = {}
    used_ids = set()

    for index, mask in enumerate(masks):
        object_id = safe_object_id(mask.name)
        base_id = object_id
        counter = 2
        while object_id in used_ids:
            object_id = f"{base_id}_{counter}"
            counter += 1
        used_ids.add(object_id)

        mesh = mask_to_mesh(
            mask.data,
            mask.affine,
            name=mask.name,
            provenance=mask.provenance,
            step_size=mesh_step_size,
        )
        obj_path = f"meshes/{object_id}.obj"
        mesh_files[obj_path] = mesh_to_obj(mesh)
        objects.append(
            {
                "object_id": object_id,
                "name": mask.name,
                "obj_path": obj_path,
                "source_mask": mask.name,
                "provenance": mask.provenance,
                "evidence_class": "DERIVED / UNREVIEWED",
                "mesh_summary": mesh.summary(),
                "surface_area_mm2": mesh_surface_area_mm2(mesh),
            }
        )

    known = {x["object_id"] for x in objects}
    unknown_motion = [m.structure_id for m in motions if m.structure_id not in known]
    if unknown_motion:
        raise ValueError(
            "Motion references unknown Blender object id(s): " + ", ".join(unknown_motion)
        )

    manifest = {
        "schema_version": 1,
        "app": "MedForge Imaging Studio",
        "title": title,
        "scene_class": "ILLUSTRATIVE / DERIVED",
        "frame_start": 1,
        "frame_end": max(2, int(frame_end)),
        "fps": max(1, int(fps)),
        "width": max(320, int(width)),
        "height": max(240, int(height)),
        "render_video": bool(render_video),
        "output_blend": "outputs/medforge_scene.blend",
        "output_video": "outputs/medforge_scene.mp4",
        "objects": objects,
        "motions": motion_manifest(motions)["motions"],
        "evidence_rules": {
            "source_dicom_included": False,
            "masks_are_derived": True,
            "motion_is_inferred_by_software": False,
            "motion_requires_external_basis": True,
            "animation_proves_diagnosis_or_causation": False,
            "visual_label": "ILLUSTRATIVE / DERIVED",
        },
    }

    repo_root = Path(__file__).resolve().parents[2]
    blender_script = repo_root / "scripts" / "blender_medforge_scene.py"
    if not blender_script.is_file():
        raise FileNotFoundError(blender_script)

    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("scene.json", json.dumps(manifest, indent=2))
        for path, raw in mesh_files.items():
            zf.writestr(path, raw)
        zf.writestr("blender_medforge_scene.py", blender_script.read_bytes())
        zf.writestr(
            "README_EVIDENCE_BOUNDARIES.txt",
            (
                "MEDFORGE BLENDER BUNDLE\n\n"
                "OBJ meshes are geometric reconstructions of DERIVED segmentation masks.\n"
                "They are not source DICOM and do not independently validate anatomical labels.\n"
                "Motion values are user/record-specified and ILLUSTRATIVE unless separately measured/cited.\n"
                "The rendered animation is not proof of diagnosis, pathology, or causation.\n"
                "Raw DICOM files and headers are intentionally excluded.\n"
            ),
        )
    return out.getvalue()


def blender_available() -> bool:
    return shutil.which("blender") is not None


def blender_bundle_command(
    extracted_bundle_dir: str | Path,
    *,
    render_video: bool = False,
    blender_executable: str = "blender",
) -> list[str]:
    root = Path(extracted_bundle_dir)
    script = root / "blender_medforge_scene.py"
    scene = root / "scene.json"
    command = [
        blender_executable,
        "--background",
        "--python",
        str(script),
        "--",
        "--scene",
        str(scene),
    ]
    if render_video:
        command.append("--render")
    return command
