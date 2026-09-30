# Forge Live Acceptance Runbook

This runbook defines the evidence required to move a capability from **implemented / fixture-tested** to **live-engine-tested** and finally **visually or user reviewed**.

A passing automated test is necessary but is not sufficient for a live-quality claim.

## Acceptance states

| State | Meaning |
|---|---|
| Implemented | Code path exists and is reachable. |
| Fixture-tested | Automated tests pass with synthetic/stubbed inputs. |
| Live-engine-tested | The real engine/provider ran on the target machine and produced preserved artifacts. |
| Human-reviewed | A reviewer scored the real artifacts against the published rubric. |
| Accepted | Required thresholds passed, critical defects are zero, and evidence is archived. |

Do not skip states.

## Evidence packet

Every live run gets a dated folder under a local, ignored acceptance-results directory. Do not commit large generated media, PHI, secrets, model weights, or private user data.

Required metadata:
- Forge commit SHA and version.
- Windows build / machine identifier.
- CPU, RAM, GPU and VRAM.
- Engine/provider names and versions.
- Model/workflow/voice identifiers.
- Exact route requested and route actually used.
- Start/end timestamps and runtime.
- Input/prompt/script identifier.
- Output file names plus hashes.
- Reviewer name/initials and review date.
- Scores, defects, screenshots or recordings, and final disposition.

Recommended local layout:

```
acceptance-results/
  YYYYMMDD-HHMM-<run-id>/
    manifest.json
    visual-scorecard.json
    narrator-scorecard.json
    windows-scorecard.json
    notes.md
    artifacts/
```

## Gate A — Blender / ComfyUI visual quality

Run at least these benchmark scenarios for each route being claimed:
1. **Character continuity** — same character, clothing, key prop and environment across 4+ shots.
2. **Camera / motion** — push, pan/tracking, medium action, and a transition shot.
3. **Lighting / composition** — readable focal hierarchy, stable exposure and no accidental clipping.
4. **Complex scene** — foreground/background separation, multiple objects, no obvious geometry or diffusion failure.
5. **Product-specific test** — GrimForge cinematic sequence or MedForge educational anatomy/mechanism sequence.

Preserve prompts, seeds when available, workflow/model identity, generated media and manifests.

Score each category 1–5:
- prompt/brief fidelity
- visual coherence
- temporal or shot-to-shot continuity
- anatomy/geometry integrity where relevant
- composition and lighting
- motion/camera quality
- artifact rate
- text/UI contamination
- product suitability
- overall presentation quality

**Pass threshold:** average >= 4.0/5, no category below 3, and zero critical defects.

Critical visual defects include corrupted media, severe flicker, broken anatomy/geometry that changes meaning, unreadable output, identity collapse across adjacent shots, silent fallback to a different medium, or labeling previs as final cinematic output.

## Gate B — Narrator quality

Render the same fixed evaluation script through every narrator/provider being considered. Save raw WAV/MP3 plus provider, voice, model, speed and normalization metadata.

Evaluate:
- intelligibility
- naturalness
- prosody/emphasis
- pacing
- pronunciation
- accent consistency
- noise/artifacts
- clipping/distortion
- emotional fit
- long-form fatigue

Use a 1–5 scale.

**Pass threshold:** average >= 4.0/5, intelligibility >= 4, naturalness >= 4, zero clipping/dropouts, and provider/voice identity shown to the user.

The system must never silently fall back to a basic system voice while reporting a premium/local narrator.

## Gate C — Windows target-PC behavior

Run on the actual supported Windows PC, not only CI.

Required phases:
1. clean preflight / dependency detection
2. first install
3. first launch
4. create sample user state
5. in-place upgrade
6. verify state preservation
7. reboot / relaunch
8. optional-engine offline behavior
9. repair/recovery path
10. uninstall boundary, if supported

Preserve before/after manifests and logs. The helper script in
`_FORGE_INTERNAL/verification/live_acceptance/windows_acceptance.ps1`
captures machine facts and file manifests without deleting user data.

**Pass threshold:** no user data loss; Forge Home/Vault/settings/outputs preserved; known shortcuts correct; app/core relaunch succeeds; missing optional engines produce explicit degraded-state messaging rather than fake success; no security setting must be disabled.

## Gate D — CareFlow real-participant UX research

The committed CareFlow demo remains simulated until actual participant sessions are completed.

Real-participant findings require:
- eligibility screening
- informed consent
- no PHI collection
- moderator script
- task-level timestamps/outcomes
- observation separated from interpretation
- participant-coded notes
- synthesis with source traceability
- contradictory evidence retained
- limitations documented
- findings supported by at least two independent evidence points unless explicitly labeled preliminary

Use `portfolio/careflow-research-lab/REAL_PARTICIPANT_STUDY_PROTOCOL.md`.

## Decision rule

A capability may be labeled **Accepted** only when:
- automated gates pass;
- the relevant live engine / target PC / participant study actually ran;
- evidence is preserved;
- the published threshold passes;
- critical defects are zero;
- limitations remain visible.

If a run fails, preserve the failed evidence, fix the issue, and create a new run. Do not overwrite failed runs or lower thresholds to make a release pass.
