from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import List


EVIDENCE_LANES = {
    "Source observation": "Describe only what is visibly present in the source image.",
    "Measurement": "Record a distance, angle, displacement, ratio, or other measured quantity.",
    "Possible mechanism": "A hypothesis about how structures could move, load, compress, stretch, or interact.",
    "Record-backed interpretation": "An interpretation explicitly supported by a radiology report, clinician note, operative report, or other cited record.",
}

MECHANISM_TYPES = [
    "Compression",
    "Traction",
    "Shear",
    "Torsion / rotation",
    "Translation / displacement",
    "Impact",
    "Dynamic / positional narrowing",
    "Instability / recurrent displacement",
    "Custom",
]

ANALYSIS_ENGINES = {
    "Manual / source-faithful": {
        "status": "connected",
        "role": "Human-authored observations, labels, measurements, and hypotheses.",
        "notes": "No automated diagnosis. Source pixels remain unchanged.",
    },
    "MedGemma multimodal": {
        "status": "planned",
        "role": "Medical image/text comprehension assistant.",
        "notes": "Use for structured observations and questions, not autonomous diagnosis. Requires a configured inference endpoint and accepted model terms.",
    },
    "MONAI Label": {
        "status": "planned",
        "role": "Interactive and automated medical-image annotation / segmentation.",
        "notes": "Best suited to radiology volumes and label workflows; can run locally or as a separate service.",
    },
    "TotalSegmentator": {
        "status": "planned",
        "role": "CT/MR anatomical segmentation.",
        "notes": "Useful for anatomy masks and 3D reconstruction. Not a medical device and not a diagnosis engine.",
    },
}


@dataclass
class ImageLabel:
    id: str
    name: str
    lane: str
    note: str
    x: int = 50
    y: int = 50
    confidence: str = "Unspecified"
    source_ref: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MechanismStep:
    id: str
    title: str
    narration: str
    visual: str
    epistemic_status: str
    source_link: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def stable_id(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:10]


def label_from_dict(data: dict) -> ImageLabel:
    allowed = {field.name for field in ImageLabel.__dataclass_fields__.values()}
    clean = {k: v for k, v in data.items() if k in allowed}
    clean.setdefault("id", stable_id(str(clean.get("name", "label")), str(clean.get("note", ""))))
    return ImageLabel(**clean)


def mechanism_step_from_dict(data: dict) -> MechanismStep:
    allowed = {field.name for field in MechanismStep.__dataclass_fields__.values()}
    clean = {k: v for k, v in data.items() if k in allowed}
    clean.setdefault("id", stable_id(str(clean.get("title", "step")), str(clean.get("narration", ""))))
    return MechanismStep(**clean)


def build_mechanism_steps(
    region: str,
    structures: str,
    mechanism: str,
    motion: str,
    hypothesis: str,
    source_ref: str = "",
) -> List[MechanismStep]:
    region = region.strip() or "the region of interest"
    structures = structures.strip() or "the labeled structures"
    motion = motion.strip() or "the proposed movement"
    hypothesis = hypothesis.strip() or "the proposed mechanism"

    raw = [
        (
            "Source anatomy",
            f"Begin with the source image and identify {structures} in {region}.",
            "Hold the source-locked image unchanged. Highlight only the structures that were labeled or documented.",
            "SOURCE-OBSERVED",
        ),
        (
            "Neutral relationship",
            f"Establish the baseline spatial relationship of {structures} before the proposed motion.",
            "Create a simplified anatomy overlay aligned to the source. Do not invent pathology that is not documented.",
            "ILLUSTRATIVE BASELINE",
        ),
        (
            "Applied motion / load",
            f"Illustrate {motion} as a possible loading condition.",
            f"Animate a transparent vector or skeletal motion showing {motion}. Keep the source image separate from the reconstruction.",
            "HYPOTHESIZED MOTION",
        ),
        (
            f"Potential {mechanism.lower()}",
            f"Show how {mechanism.lower()} could affect {structures} if the proposed relationship occurs.",
            f"Use an anatomy reconstruction to demonstrate potential {mechanism.lower()} without presenting it as proven.",
            "POSSIBLE MECHANISM",
        ),
        (
            "Potential downstream effect",
            f"Illustrate the specific hypothesis: {hypothesis}.",
            "Show the proposed consequence with a distinct hypothetical overlay and an uncertainty label.",
            "HYPOTHESIZED EFFECT",
        ),
        (
            "Return to evidence",
            "End by returning to the original source and separating what was observed from what was reconstructed.",
            "Split screen: source image on the left, illustrative mechanism on the right. List the evidence lane for each claim.",
            "EVIDENCE CHECK",
        ),
    ]
    return [
        MechanismStep(
            id=f"M{i:02d}",
            title=title,
            narration=narration,
            visual=visual,
            epistemic_status=status,
            source_link=source_ref,
        )
        for i, (title, narration, visual, status) in enumerate(raw, start=1)
    ]


def build_medical_vlm_prompt(modality: str, region: str, question: str = "") -> str:
    modality = modality.strip() or "medical image"
    region = region.strip() or "region of interest"
    q = question.strip()
    extra = f"\nUser question: {q}" if q else ""
    return f"""You are assisting with source-faithful medical image review.

Image context: {modality}; region: {region}.

Return four clearly separated sections:
1. VISIBLE OBSERVATIONS — only features that can be directly seen in the supplied image.
2. ORIENTATION / ANATOMY — identify structures and orientation only when reasonably supported.
3. UNCERTAINTY / LIMITATIONS — artifacts, missing sequences/views, resolution limits, and anything that cannot be determined.
4. QUESTIONS FOR CLINICAL CORRELATION — what report, exam, measurement, sequence, or specialist input would help resolve uncertainty.

Do not diagnose disease from a single image. Do not infer causation. Do not claim a mechanism is proven. Do not invent measurements. If a finding requires a measurement, say what should be measured. Distinguish image observations from any user-provided history.{extra}"""


def build_render_manifest(title: str, source_name: str, labels: List[ImageLabel], steps: List[MechanismStep]) -> dict:
    return {
        "schema_version": 1,
        "app": "MedForge Imaging Studio",
        "title": title,
        "stage": "planned",
        "honesty": (
            "This manifest describes a source-faithful educational reconstruction. "
            "It is not a diagnosis, medical device output, or proof of causation."
        ),
        "source_name": source_name,
        "labels": [x.to_dict() for x in labels],
        "mechanism_steps": [x.to_dict() for x in steps],
        "render_rules": {
            "preserve_source_pixels": True,
            "source_and_reconstruction_visually_distinct": True,
            "show_epistemic_status_on_each_reconstruction_step": True,
            "do_not_present_hypothesis_as_observation": True,
            "return_to_source_at_end": True,
        },
    }
