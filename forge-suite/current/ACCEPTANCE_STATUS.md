# Forge v0.5.6 — Workflow Recovery + Defense PDF Restoration acceptance status

**Release status: implementation candidate. Automated and fixture gates pass. The live-acceptance process is now defined and CI-protected, but real Blender/ComfyUI visual quality, narrator quality, and Windows target-PC behavior remain pending until preserved live runs meet the published thresholds.**

| Requirement | Status |
|---|---|
| GrimForge one-click no longer hard-stops on missing 2.5D image workflow when Blender is available | Implemented. Preflight reports exact/fallback route; Blender still → 2.5D camera-motion fallback is recorded in the manifest. |
| GrimForge 3D / 2.5D / 2D selector preserved | Implemented. Exact route remains preferred; fallback can be disabled by the user. |
| Evidence Auditor produces real defense-style PDFs | Implemented and fixture-tested. Front matter includes source-control rules, evidence-lane map, inventory, source-linked chronology, issue map, reviewer/examiner questions, source index, bookmarks and intact exhibits. |
| PDF source integrity | Fixture-tested. Original PDF second page remains present; source bookmarks remain; lossless page splitting retained. |
| MedForge end-to-end workflow | Implemented. One-click source image → analysis → teaching structure → generated visual when available / Blender still fallback → genuine Blender 3D → teaching PDF. |
| MedForge optional-engine behavior | Fixture-tested with ComfyUI/Blender absent: PDF still completes instead of dead-ending. Windows Blender outputs remain to be visually reviewed. |
| Python / JavaScript syntax | Passed. |
| Evidence / media workflow fixtures | 35 checks passed after v0.5.6 recovery additions. |
| UI regression gate | Passed. |
| Forge Learn sync | 28 required / 28 covered / 100%. |
| Live acceptance procedure | Defined in [LIVE_ACCEPTANCE_RUNBOOK.md](LIVE_ACCEPTANCE_RUNBOOK.md) and protected by CI process checks. This verifies the procedure exists; it does not mark the live tests passed. |
| Real Blender / ComfyUI visual quality | **Pending live run + human review.** Pass requires mean >= 4.0/5, no category below 3, zero critical defects, preserved engine/model/workflow metadata and reviewed final sequences. |
| Real narrator quality | **Pending live run + human review.** Pass requires mean >= 4.0/5, intelligibility and naturalness >= 4, no clipping/dropouts, and no silent provider/voice substitution. |
| Windows install / upgrade / recovery | **Pending target-PC run.** Before/after manifests, preserved Forge Home/Vault/settings/outputs, restart behavior, shortcut state and degraded-engine behavior must be reviewed. |
| CareFlow real-participant findings | Tracked separately in the portfolio study. Simulated findings remain simulated until the real-participant protocol is completed. |
