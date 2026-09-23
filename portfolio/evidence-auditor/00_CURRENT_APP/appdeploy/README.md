# Elias + Evidence Auditor — AppDeploy Development Snapshot

This folder is the GitHub development snapshot of the deployed Elias application.

## Snapshot origin

- AppDeploy app: `elias-evidence-assistant-simscb`
- Snapshot source version: `1789862851694`
- Existing deployed URL: https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

The deployed AppDeploy build remains the currently live application until a later deployment is performed. GitHub `main` contains the newer unified product work described below.

## Unified product architecture

- **Elias** — the single user-facing intelligence engine and assistant
- **Evidence Cloud** — shared user-scoped evidence layer
- **Evidence Auditor** — flagship support / contradiction / gap / provenance / chronology / reviewer-readiness workspace
- **Health + Neuro lens** — contextual medical, neurologic, and functional evidence reasoning invoked by Elias when needed
- **Packet building** — verified-evidence assembly capability invoked by Elias
- **Citation verification** — claim-to-source and quote-integrity capability invoked by Elias
- **Document composition** — evidence-backed organization and formatting capability invoked by Elias

The floating assistant is always Elias. Workspace context and user intent determine which capabilities/tools run behind the scenes.

## Evidence Cloud work now present in GitHub

The snapshot now includes development work for:

- existing authenticated private Case Vault promoted into the shared Evidence Cloud
- upload/index once, reuse across every Elias workspace and capability
- transparent evidence categories
- source locators and storage status
- heuristic candidate dates and document types
- advisory likely-duplicate groups
- advisory possible-version groups
- saved user-scoped Evidence Bundles that reference original source IDs
- app-aware Copilot actions: Find, Compare, Explain, Organize, Link, Draft, Build, Verify, Export
- clear human-verification and original-source-control boundaries
- explicit under-5-MB export target language without a false compression guarantee

## Data boundary

Original-source control is mandatory. AI summaries, labels, classifications, interpretations, diagrams, and generated filing prose must remain distinguishable from the original record.

Duplicate/version and smart-metadata results are review aids. The app must not automatically delete, replace, or rewrite original evidence based on those heuristics.

## Security / compliance boundary

Do not describe this project as HIPAA compliant merely because it uses authenticated private storage. HIPAA claims require verification of the actual deployed infrastructure, data flows, operational controls, applicable contracts/BAA, access controls, retention, logging, and related requirements.

No secrets or real patient records belong in this public repository.

## Deployment note

Deployment is intentionally separate from this GitHub work. When deployment capacity is available again, use this folder as the development source to reconcile into the next AppDeploy release and run the regression suite first.
