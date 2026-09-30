# Narrator Quality Acceptance Rubric

Evaluate real narrator output with a fixed script and identical text across providers/voices.

## Fixed evaluation script

> At first light, the station appears quiet. Look closer and the story changes: warning lamps pulse along the outer ring, the reactor tone drops half a step, and a maintenance crew stops where the corridor narrows. The narrator should sound composed, human, and deliberate—not rushed, metallic, theatrical by accident, or exhausted by the end of a longer passage.

Also include:
- at least three proper nouns used by the product
- one acronym
- one sentence with numbers
- one emotionally restrained sentence
- one 90–120 second long-form passage

## Score 1–5

- intelligibility
- naturalness
- prosody and emphasis
- pacing
- pronunciation
- accent consistency
- noise/artifacts
- clipping/distortion
- emotional fit
- long-form listening comfort

## Objective checks

Record:
- sample rate and channels
- peak level / whether clipping occurred
- unexpected silence/dropouts
- duration
- provider, model, voice and speed
- whether normalization/mastering ran

## Pass

- overall mean >= 4.0
- intelligibility >= 4
- naturalness >= 4
- no clipping or unexplained dropout
- no silent substitution to another provider/voice
- active provider and voice are visible in the UI/manifest

A synthetic fixture or silent WAV verifies assembly only; it never passes narrator quality.
