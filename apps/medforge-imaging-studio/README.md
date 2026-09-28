# MedForge Imaging Studio

MedForge is a source-faithful medical imaging and mechanism-visualization app derived from the Forge engine.

## Purpose

MedForge is for:
- reviewing medical images while preserving the original source pixels
- labeling anatomy, observations, measurements, hypotheses, and record-backed interpretations
- keeping evidence lanes visually separate
- building illustrative injury/pathology mechanism storyboards
- generating playable educational animatics
- exporting provider-neutral analysis prompts and render manifests

MedForge is **not** a diagnostic device and should not turn a single image into a definitive diagnosis or proof of causation.

## Current prototype

### Source support
- PNG
- JPG/JPEG
- WebP
- single-frame DICOM (.dcm)

For DICOM, the prototype renders the pixel data to an image for the project workspace. Raw DICOM headers are not exported into the MedForge project JSON.

### Evidence lanes
1. Source observation
2. Measurement
3. Possible mechanism
4. Record-backed interpretation

Every label can carry a confidence/support state and a source/reference note.

### Mechanism Synthesizer

The local deterministic mechanism engine creates a six-step sequence:
1. source anatomy
2. neutral relationship
3. applied motion/load
4. potential mechanical interaction
5. hypothesized downstream effect
6. return-to-evidence comparison

Synthesized steps are explicitly labeled as illustrative/hypothesized and remain separate from the source image.

### Planned analysis adapters

- **MedGemma multimodal** — medical image/text comprehension
- **MONAI Label** — interactive and automated medical annotation
- **TotalSegmentator** — CT/MR anatomical segmentation and 3D reconstruction inputs

These are architectural targets, not connected inference services in the initial prototype.

## Run locally

```bash
cd apps/medforge-imaging-studio
python -m pip install -r requirements.txt
streamlit run app.py
```

## Privacy design

- The source image is locked and never overwritten.
- Exported projects do not include raw DICOM headers.
- Patient-identifying metadata should be removed before external sharing.
- A future DICOM-series pipeline should explicitly de-identify metadata before cloud inference or collaboration.

## Render contract

A MedForge render must:
- preserve the original source pixels
- distinguish source imagery from reconstructed anatomy
- display the epistemic status of mechanism steps
- never relabel a hypothesis as an observation
- return to the original evidence at the end

## Relationship to GrimForge

MedForge reuses Forge concepts—source lock, scene planning, narration, animatics, render manifests—but has a separate medical/evidence interface. This keeps the creative war-film product clean while allowing a shared rendering core underneath both apps.


## DICOM study + 3D volume workflow

The current branch now adds:
- multiple DICOM file or ZIP upload
- PHI-minimized series inspection
- series selection by SeriesInstanceUID
- geometric slice ordering using ImagePositionPatient + ImageOrientationPatient when available
- rescale slope/intercept handling
- source-locked z-y-x volume assembly
- axial / coronal / sagittal multiplanar reconstruction
- downsampled browser 3D intensity preview
- compressed DICOM decoder support through pylibjpeg plugins
- explicit decode warnings when a series cannot be assembled

Raw pydicom Dataset objects are not included in project JSON exports.

## Segmentation path

The branch now proves the mask pipeline with a deliberately non-clinical percentile mask. This mask has **no anatomical meaning**. It exists so the mask viewer/render plumbing can be tested before connecting anatomical segmentation.

Planned reviewed adapters:
- TotalSegmentator
- MONAI Label

Both adapters are represented as provider-neutral job contracts and remain marked planned until a real worker is connected and validated.

## Parallel learning app

The sibling app `apps/medforge-build-lab/` teaches the same pipeline step by step. It imports the actual MedForge modules and uses source introspection so lesson code stays synchronized with the app.

The Build Lab includes:
- source → privacy → series → volume → MPR → 3D preview → mask/segmentation → image understanding → mechanism → export pipeline map
- plain-English explanations
- input/output for each step
- why the step matters
- failure modes and repair paths
- current unit-test strategy
- actual live function source code
- a synthetic 3D phantom sandbox with axial/coronal/sagittal controls
