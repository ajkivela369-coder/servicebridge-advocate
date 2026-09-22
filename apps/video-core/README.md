# Shared Cinematic Render Pipeline

Provider-neutral contracts shared by WildTake, GrimForge Cinema, and future video apps.

## Purpose

The apps should share one production model rather than each inventing separate video, voice, caption, and QC logic.

A render job moves through:

1. rights preflight
2. source / reference ingestion
3. beat or shot planning
4. script / dialogue
5. video generation or uploaded takes
6. narration / dialogue synthesis
7. captions
8. audio mix
9. continuity checks
10. render
11. final QC
12. export

## Honesty rule

A workflow state must distinguish:
- planned
- preview
- generated
- rendered
- QC passed
- export ready

Storyboard or placeholder content must never be labeled as a rendered final video.

## Quality targets

The phrase "highest available" means the best settings actually supported by the connected provider. It is not a claim of Sora, 4K, HDR, or any other capability unless the selected provider reports that capability.

## Audio lanes

- dialogue / narration
- source ambience
- room tone
- Foley / SFX
- music

The mixing layer should support ducking, fades, crossfades, loudness targets, peak limiting, and clipping checks.

## Continuity

Shared continuity metadata includes character IDs, set IDs, wardrobe/prop invariants, camera/lens rules, lighting, screen direction, and adjacent-shot checks.

## Rights

Every job carries a rights basis and optional attribution metadata. Unknown provenance remains flagged. Transformation/commentary does not itself guarantee fair use.

## Files

- `pipeline.py` — provider-neutral data model, provider selection, and QC baseline.
- `render_job.schema.json` — portable JSON contract for TypeScript/Python/front-end integrations.
