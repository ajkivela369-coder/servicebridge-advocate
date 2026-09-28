from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List
import tempfile
import zipfile

import nibabel as nib
import numpy as np


@dataclass
class MaskVolume:
    name: str
    data: np.ndarray
    affine: np.ndarray
    source_format: str
    provenance: str = "user-imported segmentation"

    @property
    def shape(self):
        return tuple(int(x) for x in self.data.shape)

    @property
    def voxel_count(self):
        return int(np.count_nonzero(self.data))

    def safe_summary(self) -> dict:
        return {
            "name": self.name,
            "shape": list(self.shape),
            "voxel_count": self.voxel_count,
            "source_format": self.source_format,
            "provenance": self.provenance,
            "review_status": "unreviewed",
        }


def _load_nifti_bytes(raw: bytes, name: str, provenance: str) -> MaskVolume:
    if not raw:
        raise ValueError(f"{name} is empty.")
    suffix = ".nii.gz" if name.lower().endswith(".nii.gz") else ".nii"
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(raw)
        tmp.flush()
        img = nib.load(tmp.name)
        data = np.asarray(img.dataobj)
        affine = np.asarray(img.affine, dtype=np.float64)

    if data.ndim != 3:
        raise ValueError(f"{name}: expected a 3D mask volume, got shape {data.shape}.")
    if not np.isfinite(data).any():
        raise ValueError(f"{name}: mask contains no finite voxels.")

    # TotalSegmentator exports binary class masks. For broader compatibility,
    # treat every positive value as part of the imported mask while preserving
    # the original image separately from this derived segmentation.
    mask = np.asarray(data > 0, dtype=bool)
    return MaskVolume(
        name=Path(name).name,
        data=mask,
        affine=affine,
        source_format="NIfTI",
        provenance=provenance,
    )


def load_mask_upload(raw: bytes, name: str, provenance: str = "user-imported segmentation") -> List[MaskVolume]:
    """
    Load one NIfTI file or a ZIP containing NIfTI masks.

    This loader deliberately ignores unrelated files inside archives and does
    not infer that a filename is clinically correct. The filename is treated
    only as an external label until a human reviews it.
    """
    lower = name.lower()
    if lower.endswith(".nii") or lower.endswith(".nii.gz"):
        return [_load_nifti_bytes(raw, name, provenance)]

    if lower.endswith(".zip"):
        masks: List[MaskVolume] = []
        try:
            with zipfile.ZipFile(BytesIO(raw)) as zf:
                for member in zf.infolist():
                    if member.is_dir():
                        continue
                    member_name = member.filename.replace("\\", "/").split("/")[-1]
                    lower_member = member_name.lower()
                    if not (lower_member.endswith(".nii") or lower_member.endswith(".nii.gz")):
                        continue
                    if member.file_size > 512 * 1024 * 1024:
                        continue
                    masks.append(
                        _load_nifti_bytes(
                            zf.read(member),
                            member_name,
                            provenance,
                        )
                    )
        except zipfile.BadZipFile as exc:
            raise ValueError(f"{name} is not a readable ZIP archive.") from exc
        if not masks:
            raise ValueError(f"{name} did not contain any .nii or .nii.gz mask files.")
        return masks

    raise ValueError("Mask import supports .nii, .nii.gz, or ZIP archives containing NIfTI masks.")


def mask_mpr(mask: np.ndarray, z: int, y: int, x: int):
    if mask.ndim != 3:
        raise ValueError("Expected a 3D mask.")
    z = int(np.clip(z, 0, mask.shape[0] - 1))
    y = int(np.clip(y, 0, mask.shape[1] - 1))
    x = int(np.clip(x, 0, mask.shape[2] - 1))
    return (
        mask[z, :, :],
        np.flipud(mask[:, y, :]),
        np.flipud(mask[:, :, x]),
    )


def mask_alignment_note(mask: MaskVolume, source_shape) -> dict:
    source_shape = tuple(int(x) for x in source_shape) if source_shape is not None else None
    same_shape = source_shape == mask.shape if source_shape is not None else False
    return {
        "same_array_shape": same_shape,
        "source_shape": list(source_shape) if source_shape is not None else None,
        "mask_shape": list(mask.shape),
        "overlay_allowed": False,
        "reason": (
            "Array shapes match, but MedForge still requires spatial-affine validation before overlay."
            if same_shape
            else "Mask and source array shapes differ; resampling/alignment is required before overlay."
        ),
    }
