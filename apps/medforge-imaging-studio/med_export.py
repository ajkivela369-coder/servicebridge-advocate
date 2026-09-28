from __future__ import annotations

import base64
from io import BytesIO
import json
import tempfile
import zipfile

import nibabel as nib
import numpy as np


def nifti_mask_bytes(mask) -> bytes:
    """Serialize a MedForge MaskVolume back to NIfTI while preserving its affine."""
    img = nib.Nifti1Image(
        np.asarray(mask.data, dtype=np.uint8),
        np.asarray(mask.affine, dtype=np.float64),
    )
    with tempfile.NamedTemporaryFile(suffix=".nii.gz") as tmp:
        nib.save(img, tmp.name)
        tmp.flush()
        return open(tmp.name, "rb").read()


def build_render_bundle(
    manifest: dict,
    masks: list,
    source_preview_data_uri: str = "",
    include_source_preview: bool = False,
) -> bytes:
    """
    Build a portable MedForge -> Forge package.

    Raw DICOM objects are never added here. The bundle contains only:
    - render manifest JSON
    - derived NIfTI masks
    - optional rendered source-preview PNG/JPEG
    - an evidence-boundary README
    """
    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "medforge-render-manifest.json",
            json.dumps(manifest, indent=2, default=str),
        )

        for mask in masks:
            safe_name = mask.name.replace("/", "_").replace("\\", "_")
            if not safe_name.lower().endswith(".nii.gz"):
                safe_name += ".nii.gz"
            zf.writestr(f"masks/{safe_name}", nifti_mask_bytes(mask))

        if include_source_preview and source_preview_data_uri:
            try:
                header, encoded = source_preview_data_uri.split(",", 1)
                raw = base64.b64decode(encoded)
                ext = "jpg" if "jpeg" in header.lower() else "png"
                zf.writestr(f"source/source_preview.{ext}", raw)
            except Exception as exc:
                zf.writestr(
                    "source/PREVIEW_NOT_INCLUDED.txt",
                    f"Could not decode source preview: {type(exc).__name__}: {exc}",
                )

        zf.writestr(
            "README_EVIDENCE_BOUNDARIES.txt",
            (
                "MEDFORGE -> FORGE RENDER BUNDLE\n\n"
                "SOURCE imaging and DERIVED segmentation are different evidence classes.\n"
                "NIfTI masks in /masks are DERIVED segmentation outputs and require human review.\n"
                "Mechanism animation is ILLUSTRATIVE unless a step is explicitly source-observed or record-backed.\n"
                "Raw DICOM files and DICOM headers are not included in this bundle.\n"
                "Do not infer diagnosis or causation from the animation itself.\n"
            ),
        )
    return out.getvalue()
