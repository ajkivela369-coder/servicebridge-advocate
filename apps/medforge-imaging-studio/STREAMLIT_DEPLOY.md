# Free Streamlit deployment

MedForge and MedForge Build Lab are both Streamlit applications and can be deployed on Streamlit Community Cloud from the GitHub repository.

## App 1 — MedForge Imaging Studio

Repository:
`ajkivela369-coder/servicebridge-advocate`

Branch:
`feature/medforge-imaging-studio`

Main file:
`apps/medforge-imaging-studio/app.py`

## App 2 — MedForge Build Lab

Repository:
`ajkivela369-coder/servicebridge-advocate`

Branch:
`feature/medforge-imaging-studio`

Main file:
`apps/medforge-build-lab/app.py`

## Recommended first public preview

Deploy Build Lab first because it uses synthetic/public data and does not need personal imaging.

For Imaging Studio, keep the first public deployment as a development/demo environment. Use public or de-identified imaging while privacy/storage behavior is being validated.

## Compute split

Streamlit Community Cloud:
- UI
- source/image review
- DICOM series assembly for modest studies
- MPR
- mask import
- mechanism planning
- Build Lab

Local machine or free Colab:
- TotalSegmentator
- heavier segmentation workloads
- later MONAI Label worker

This split keeps the public app lightweight and avoids paying for always-on GPU hosting.
