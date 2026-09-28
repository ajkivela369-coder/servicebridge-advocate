# Forge v0.5.4 Product Completion Blueprint

Status: accepted product contract, 28 September 2026. This document preserves AJ's product decisions. The bundled implementation is a candidate, not a completed release. A blocked requirement remains part of the contract; it cannot be removed to make the gate pass.

## Product identities

| Product | Fundamental role | Canonical identity |
|---|---|---|
| Forge Workspace | Core, models, storage, backups, app launch, health, updates | Electric blue/cyan core emblem |
| Elias | Independent general assistant: conversation, reasoning, writing, documents, research, tools | Emerald green Elias figure |
| Evidence Auditor | Ingestion, analysis, provenance, contradictions, administrative/benefits packets | Violet/purple scales |
| MedForge | Medical image/mechanism analysis, educational visualization and media | Crimson/red medical emblem |
| GrimForge | Story, imagery, voice, animation and full-episode production | Orange/gold dragon |
| Forge Learn | Explain how every production capability was built and works | Bright blue illuminated book |

One Forge Core supplies model routing, tool execution and media services. One shared Copilot layer receives app-specific context, tools, grounding rules and personality. Do not build separate weak chatbot stacks. Workspace and Learn remain separate products. Evidence Auditor is an optional tool for Elias, not its prerequisite.

## Elias acceptance contract

Standalone new chats, history, attachments, general reasoning, writing/coding, research, project/case memory, model routing and tool use. Explicitly distinguish general, document-aware and case-aware work. Evidence access is optional. Model quality is an independent requirement: changing the interface or the system prompt does not establish parity with ChatGPT. Stronger local models and optional confirmed hybrid services must be evaluated on real tasks, with memory limits and actual model identity visible.

Required workflow: new conversation → answer → retain context → attach document → ask about document. Test with the real model, not a canned answer. Research requires a real retrieval path, not unsupported claims that browsing occurred.

## Evidence Auditor acceptance contract

Prominent **Upload Evidence → Build Packet** workflow with multi-file selection and drag/drop. Accept PDF, images, DOCX, email exports, ZIP, video and audio. Preserve originals; extract/OCR/transcribe/index; categorize and identify metadata with confirmation where uncertain. Do not require pasted text for every document. Report individual failures without losing successful originals.

Build timeline, findings, contradictions and missing-evidence audit. Copilot actions: Find supporting evidence; Find contradictions; What is missing?; Build chronology; Draft this section; Trace this statement; Compare these records; Prepare packet. Assertions retain source/page or chunk references. Missing extracted text is not proof that evidence is absent. Firsthand observations, records, opinions and inference stay distinct.

Recipes: VBA, SSDI, APTD, ADA, Clinician Summary and Custom. A completed packet contains an actual usable PDF, source index, exhibits and chronology, with source-linked narrative where supported. Preserve visual exhibits. Validate submission size; when splitting, retain every page and disclose any part still over the limit. Do not substitute a JSON outline or ZIP alone for the PDF.

Required workflow: select five files → preserve → index → search → build VBA packet → download/open a real PDF. Also test each recipe and missing-engine/partial-upload behavior. Separate-case selection must not pull unrelated source material into its packet.

## GrimForge acceptance contract

Simple mode: premise, visual style, approximate runtime, narrator and **Generate Full Episode**.

Pro mode: factions, characters, story structure, scale, camera, visual style, narration, sound, violence, runtime, reference lens, continuity bible, individual scenes, render engines and Director's Notes.

Pipeline: premise → script/beats → continuity bible → storyboard → generated images/shots → voice → music/SFX plan → video/animation → captions → assembly → final playable MP4. Preserve reusable world/character/prop information and enable scene review/replacement without rebuilding the whole production. Show queue and progress.

Labels are contractual: **Local Animatic** means storyboard/text-slide planning video. **Illustrated Episode** means generated stills assembled with narration. **Full Motion Render** means generated motion shots, not an animatic renamed as a finished film. Actual image and video quality, shot continuity, narration and assembly must be reviewed together.

Default narrator should be high-quality British or Australian. Show active voice/provider; do not silently downgrade to generic system speech. Local voices remain an offline option; optional connected premium engines need real integration and explicit account/usage configuration.

Required workflow: premise → episode → scenes → voice → visual media → assembled MP4. Silent or canned test fixtures verify assembly only; they do not pass generative or voice-quality acceptance.

## MedForge acceptance contract

Image analysis, anatomy/mechanism explanation, high-quality anatomical illustrations, annotated medical figures, mechanism diagrams, progressive teaching frames and eventual 3D/pseudo-3D explanatory video. Clearly distinguish visible observations, interpretations, mechanism hypotheses, uncertainty and next verification steps. Preserve original medical images. Generated anatomical art is not a diagnostic scan or validated patient-specific geometry.

Required workflow: upload image → analysis → mechanism → generated teaching visual → export. A 3D-styled clip is not proof of an actual 3D scene/mesh/render pipeline. Higher-end outputs require visual inspection, not merely an existing file.

## Design, installer and learning contract

Use the supplied six-product design image as the visual regression reference. Dark premium family layout, readable type, consistent spacing and each app's own identity. Use one permanent icon set for browser app, app header, splash/launcher and Windows shortcuts. Green Elias, violet Evidence Auditor, crimson MedForge, orange GrimForge and blue Forge Learn must remain consistent.

One Desktop **Forge Apps** folder contains the shortcuts; create a matching Start-menu group. Remove only known loose shortcuts from previous Forge installers. Upgrade must preserve Vault, user settings, workflows and outputs and restart Core reliably. Test this on Windows, including locked-runtime behavior.

Every shipping capability has a Forge Learn lesson explaining its actual implementation, dependencies, failure modes and data shape, linking to the working app. Lesson existence and percentage coverage alone do not prove teaching accuracy.

## Build order

1. Shared Copilot/model/tool framework and explicit capability contracts.
2. Independent Elias, documents, context, memory and evaluated model routes.
3. Evidence batch intake, source grounding, audits and usable PDF exports.
4. GrimForge visual/video production and high-quality narration.
5. MedForge visual generation and teaching exports.
6. Design/icon parity, Learn synchronization and full regression testing.

## Release rule

A release fails if any required real workflow is blocked, incomplete, untested or falsely represented by a fallback. Static HTML checks and fixture tests are useful but insufficient. Keep separate statuses for implemented, fixture-tested, live-engine-tested and visually/user-reviewed. Preserve actual artifacts, engine identities and limitations in the acceptance report. Do not declare v0.5.4 complete until the real engine and Windows gates pass.


## Shared Media / 3D toolchain

Blender and FFmpeg are shared Forge dependencies, not per-app copies. The Windows installer detects existing tools before installing them. MedForge and GrimForge consume Blender through Forge Core. ComfyUI remains the optional local AI image/video layer. Elias and Evidence Auditor do not require Blender for normal use.

Acceptance: Windows install/detection → `/api/3d/status` reports the actual executable → MedForge produces an editable `.blend`, PNG and MP4 teaching scene → GrimForge produces an editable `.blend`, PNG and MP4 previs scene. Visual inspection is required. A 3D previs must not be labeled as the final cinematic render, and a MedForge teaching mesh must not be labeled patient-specific anatomy.

---

## v0.5.5 product-polish addendum

The approved GrimForge Simple concept and six-product Forge Suite design showcase are now explicit visual acceptance references under `DESIGN_REFERENCE/`.

Additional contract:

- **Every app must visually communicate its purpose before the user reads documentation.** Color, iconography, primary action, status hierarchy and result/media surfaces are product requirements.
- **GrimForge Simple** exposes an animation-style selector with exactly three user-facing families: 3D, 2.5D and 2D. Generate Full Episode runs the complete script → scene media → animation → narration → captions → MP4 pipeline for the selected route.
- 3D uses Blender; 2.5D uses generated stills with cinematic depth-style motion; 2D uses a configured generated-motion workflow. The UI must state the required engine when one is unavailable instead of silently substituting another medium.
- **Evidence Auditor** keeps Upload Evidence → Build Packet visually prominent and supports batch files and actual PDF exports.
- **Elias** remains independent. Evidence context is optional; quality-first local routing may use a larger installed reasoning model but must not claim parity with a remote frontier model without evidence.
- **MedForge and GrimForge** share media/3D infrastructure but retain separate workflows and visual identities.
- **Copilots** combine conversation with supported app actions; they should not merely be decorative chat boxes.
- A release cannot pass product UI regression if a rich product is flattened into a generic diagnostic form.
