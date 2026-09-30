# Visual Quality Acceptance Rubric

Use this for real Blender, ComfyUI, GrimForge and MedForge outputs.

Score every category from 1 (unacceptable) to 5 (portfolio/production ready). Add a short evidence note for every score <= 3.

| Category | 1 | 3 | 5 |
|---|---|---|---|
| Brief fidelity | misses core subject/action | mostly follows brief | precise subject, action, style and constraints |
| Coherence | visibly broken | usable with minor oddities | stable, intentional, believable |
| Continuity | identity/scene collapses | minor drift | strong identity, prop and environment persistence |
| Geometry/anatomy | materially wrong | minor imperfections | structurally convincing for intended use |
| Composition | confusing focus | serviceable framing | strong hierarchy and deliberate framing |
| Lighting | broken/exposure issues | mostly stable | deliberate, cinematic/readable |
| Motion/camera | unusable/jittery | acceptable motion | smooth, motivated camera and subject motion |
| Artifact control | frequent severe artifacts | occasional artifacts | rare/non-distracting artifacts |
| Contamination | unwanted text/UI/watermark-like artifacts | small distractions | clean frame |
| Product suitability | not usable for app purpose | usable draft | clearly supports claimed product experience |

## Critical defects

Any critical defect is an automatic fail:
- corrupted or unplayable output
- severe flicker or frame collapse
- identity collapse between adjacent continuity-locked shots
- anatomy/geometry failure that changes instructional meaning
- hidden fallback to a different generation medium
- output labeled "final/full motion" when it is only previs/animatic
- missing manifest/provider/model identity

## Pass

- mean score >= 4.0
- no individual category below 3
- zero critical defects
- reviewer has inspected the final assembled sequence, not only still frames

Record the exact engine, workflow/model, seed when available, render settings, requested route, actual route, duration, output hashes and reviewer/date.
