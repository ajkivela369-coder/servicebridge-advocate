# MedForge zero-cost / open-source finish path

MedForge is the coordinator. Use external open-source tools only where they add something MedForge should not reimplement from scratch.

## Recommended stack

### 1. MedForge Imaging Studio
Role: source lock, evidence lanes, DICOM series ingestion, MPR, 3D preview, imported masks, mechanism storyboard, animatic, and auditable export.

Cost: local/open-source code in this repository.

### 2. 3D Slicer
Role: manual medical-image review, segmentation correction, measurements, 3D visualization, and independent validation.

Why: mature free/open-source desktop medical-imaging platform. Keep this as the "human review" station.

### 3. TotalSegmentator
Role: generate initial CT/MR anatomical masks.

Preferred first tasks:
- `total` for CT
- `total_mr` for MR

Use:
- local machine when privacy matters
- the included Colab notebook for de-identified public/test imaging when free GPU is available

Outputs return to MedForge as NIfTI masks.

### 4. MONAI Label
Role: later interactive AI-assisted mask correction / annotation.

Do not make it a hard dependency for the first deploy. Add it once the mask import/review workflow is stable.

### 5. OHIF / Cornerstone3D
Role: future production-grade browser viewer.

MedForge's Streamlit viewer is enough to finish the first end-to-end workflow. OHIF/Cornerstone is the better long-term route for fast DICOM streaming, advanced measurements, oblique MPR, and segmentation overlays.

## Free hosting

### Streamlit Community Cloud
Good target for:
- MedForge Build Lab
- lightweight MedForge demonstrations with public/de-identified data

The app already uses Streamlit and the repository is CI-tested. Community Cloud connects directly to GitHub.

### Google Colab
Good target for:
- occasional TotalSegmentator jobs
- public/de-identified development data

Free GPU availability and usage limits are dynamic and not guaranteed.

### Hugging Face
Static Spaces are free. Current compute-backed Gradio/Docker Space creation can require a paid plan, so do not make it our default zero-cost deployment route.

## Privacy split

**Local-only path for sensitive imaging**
DICOM → local MedForge / 3D Slicer → local TotalSegmentator → masks → MedForge.

**Free-cloud development path**
De-identified/public DICOM → Streamlit/Colab → TotalSegmentator → masks → MedForge.

## Current MedForge alignment rule

Imported NIfTI masks are deliberately **not overlaid on the DICOM source yet**. Matching array dimensions is insufficient evidence that two volumes share the same patient-space orientation. We will add DICOM↔NIfTI affine validation/resampling before enabling overlays.

That restriction is a feature, not a missing safety check.
