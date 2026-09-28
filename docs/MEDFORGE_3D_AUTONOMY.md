# MedForge 3D Autonomy Layer

This layer removes the requirement for paid 3D/video services from the MedForge mechanism workflow.

## Objective

Given a source DICOM series plus reviewed/derived segmentation masks, MedForge should be able to:

1. validate source and mask geometry in patient space
2. overlay the mask only when geometry is compatible **and** the user confirms the source↔mask pairing
3. convert masks into patient-space triangle meshes
4. attach only explicit, user/record-specified rigid-body motion
5. export a self-contained Blender scene bundle
6. render the same scene without Blender through the native Python+FFmpeg fallback
7. keep DERIVED / ILLUSTRATIVE boundaries visible in every video path
8. perform optional image review through a localhost VLM in Creditless Mode

## Spatial pipeline

### DICOM
MedForge builds a z-y-x volume and a 4x4 affine mapping source voxel indices to patient RAS millimeters.

### NIfTI
Imported masks retain their original NIfTI affine.

### Geometry compatibility
`med_space.alignment_report` compares patient-space geometry rather than array shape.

A geometry-compatible result does **not** prove identity of the source/mask pair. The UI separately requires confirmation that the mask:
- was generated from the selected source series, or
- was explicitly co-registered to it.

Only then can MedForge display an aligned overlay.

### Resampling
`resample_mask_to_source` maps source-grid coordinates through patient space into the mask grid and uses nearest-neighbor interpolation so segmentation labels stay discrete.

## Mesh pipeline

`med_mesh.mask_to_mesh`:
- requires a non-empty 3D mask
- requires a finite, invertible 4x4 affine
- runs marching cubes
- transforms every vertex into patient RAS millimeters
- carries DERIVED / UNREVIEWED provenance into the mesh metadata

OBJ output is intentionally simple and portable.

## Motion pipeline

`med_motion.build_motion` does not infer biomechanics.

Motion values are explicit:
- translation in millimeters
- rotation in degrees
- start/end frame
- structure/object id
- motion-basis note

Every track remains `ILLUSTRATIVE / HYPOTHESIZED` unless a separate evidence record supports the entered values.

## Blender path

`med_blender.build_blender_scene_bundle` creates a ZIP containing:
- `scene.json`
- OBJ meshes
- `blender_medforge_scene.py`
- evidence-boundary README

Raw DICOM files and headers are excluded.

The Blender script:
- imports patient-space meshes
- attaches motion to separate controller objects
- preserves mesh provenance
- creates local camera and lighting
- burns **ILLUSTRATIVE / DERIVED** into rendered frames
- saves a .blend file
- can optionally render an H.264 MP4

Run locally:

```bash
python scripts/run_medforge_blender_bundle.py medforge-blender-bundle.zip --render
```

## Native no-Blender path

The same bundle can render without Blender:

```bash
python scripts/render_medforge_native3d_bundle.py medforge-blender-bundle.zip --output medforge-native3d.mp4
```

The native path:
- loads the patient-space OBJ meshes
- applies the same explicit motion tracks
- renders frames with Python/matplotlib
- burns an ILLUSTRATIVE / DERIVED label into every frame
- assembles the final MP4 with local FFmpeg

This makes Blender optional.

## Local vision path

MedForge can send the source image and evidence-separated review prompt to an OpenAI-compatible localhost VLM endpoint.

Creditless policy blocks non-local endpoints.

The local VLM output remains an assistive draft and does not become:
- a diagnosis
- a measurement
- a record fact
- proof of causation

without human verification.

## Dependency ladder

### Always-available / deterministic
- source image review
- evidence lanes
- manual labels
- mechanism storyboard
- local project/export manifests

### Standard local Python stack
- DICOM volume/MPR
- NIfTI mask import
- spatial alignment/resampling
- marching-cubes meshes
- native 3D rendering

### Local executables
- FFmpeg for MP4 assembly
- Blender for advanced 3D editing/rendering (optional)

### Optional local AI
- TotalSegmentator for initial segmentation
- localhost VLM for assistive image review
- local image/video generation through the shared Creditless Runtime

No paid provider is required for the core 3D mechanism workflow.

## Bundle security

Both Blender and native bundle runners use traversal-safe ZIP extraction. Archives containing absolute paths or `../` path traversal are rejected.

## Evidence rule

A visually convincing reconstruction remains a reconstruction.

The software must preserve:
- SOURCE / DERIVED distinction
- OBSERVATION / INTERPRETATION distinction
- MEASURED / ILLUSTRATIVE motion distinction
- uncertainty and provenance
