# MedForge Build Lab

A parallel teaching application for MedForge Imaging Studio.

The Build Lab is deliberately tied to the **actual MedForge modules**. It imports the same `med_io`, `med_volume`, `med_segmentation`, and `med_engine` files and uses Python introspection to display the real function source code inside each lesson.

## Learning pattern

Every step includes:
- a plain-English description
- input and output
- why the step matters
- what failure looks like
- how to repair it
- how MedForge tests it
- the actual current source code

## Interactive sandbox

The app creates a synthetic 3D phantom with no patient data and lets the learner move axial, coronal, and sagittal cursors. It also demonstrates the non-clinical mask pipeline so users can see the difference between a software mask and an anatomical segmentation.

## Run

```bash
cd apps/medforge-build-lab
python -m pip install -r requirements.txt
streamlit run app.py
```
