from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class MechanismMotion:
    structure_id: str
    start_frame: int
    end_frame: int
    translation_mm_xyz: tuple[float, float, float]
    rotation_deg_xyz: tuple[float, float, float]
    evidence_lane: str = "ILLUSTRATIVE / HYPOTHESIZED"
    note: str = ""

    def to_dict(self):
        return asdict(self)


def build_motion(
    structure_id: str,
    *,
    translation_mm_xyz=(0.0, 0.0, 0.0),
    rotation_deg_xyz=(0.0, 0.0, 0.0),
    start_frame: int = 1,
    end_frame: int = 90,
    note: str = "",
) -> MechanismMotion:
    """
    Build an explicitly illustrative rigid-body motion.

    MedForge does not infer these values from a scan. Translation/rotation must
    be user-entered, record-backed, measured, or otherwise explicitly sourced.
    """
    if not structure_id.strip():
        raise ValueError("structure_id is required.")
    start_frame = int(start_frame)
    end_frame = int(end_frame)
    if start_frame < 1 or end_frame <= start_frame:
        raise ValueError("end_frame must be greater than start_frame >= 1.")

    translation = tuple(float(x) for x in translation_mm_xyz)
    rotation = tuple(float(x) for x in rotation_deg_xyz)
    if len(translation) != 3 or len(rotation) != 3:
        raise ValueError("Translation and rotation must each have exactly 3 values.")

    return MechanismMotion(
        structure_id=structure_id.strip(),
        start_frame=start_frame,
        end_frame=end_frame,
        translation_mm_xyz=translation,
        rotation_deg_xyz=rotation,
        note=note.strip(),
    )


def motion_manifest(motions: Iterable[MechanismMotion]) -> dict:
    rows = [m.to_dict() for m in motions]
    return {
        "motions": rows,
        "evidence_rule": (
            "Motion values are illustrative/user-specified unless separately linked "
            "to a measurement or cited record. Animation is not proof of diagnosis or causation."
        ),
        "contains_inferred_motion": False,
    }
