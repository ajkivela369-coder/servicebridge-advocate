# ServiceBridge Advocate

**AJ Kivela — Applied AI, Health Data & Evidence Systems**  
**Employer-facing portfolio:** https://aj-kivela-portfolio.lovable.app

[![CI](https://github.com/ajkivela369-coder/servicebridge-advocate/actions/workflows/ci.yml/badge.svg)](https://github.com/ajkivela369-coder/servicebridge-advocate/actions/workflows/ci.yml)
[![Portfolio QC](https://github.com/ajkivela369-coder/servicebridge-advocate/actions/workflows/portfolio-qc.yml/badge.svg)](https://github.com/ajkivela369-coder/servicebridge-advocate/actions/workflows/portfolio-qc.yml)

## Portfolio highlights

- **SearchSignal — SEO + GEO Operations Lab:** [Geisel interview build](https://searchsignal-geisel-interview.vercel.app/) · [published v2](https://forgesearcher.floot.app/) — live public-URL auditing, bounded site intelligence, document/redirect checks, explainable SEO/GEO scoring, prioritization, structured-data/content tooling, analytics workflows, and WordPress support/training.
- **Application portfolio index:** [portfolio/README.md](portfolio/README.md)
- **Portfolio quality-control contract and status:** [portfolio/QUALITY_CONTROL.md](portfolio/QUALITY_CONTROL.md)
- **Step-by-step app build/upgrade index:** [portfolio/BUILD_AND_UPGRADE_INDEX.md](portfolio/BUILD_AND_UPGRADE_INDEX.md)
- **Employer-facing portfolio:** https://aj-kivela-portfolio.lovable.app/

SearchSignal and the other portfolio applications are independent project work. Demo data, connector-ready integrations, source-only prototypes, and live production functionality are labeled separately rather than being represented as paid employment or unverified production experience.

<!-- FORGE-SUITE-CURRENT:START -->
## Current Forge Suite — v0.5.6

The repository now mirrors the current integrated local Forge Suite under **[`forge-suite/current/`](forge-suite/current/)**.

- **Forge Workspace** — local control center, model/tool health, backups, shared media/3D tools, and app launch.
- **Elias** — independent local conversational/document assistant with quality-first local routing.
- **Evidence Auditor** — batch evidence intake, source provenance, chronology/review workflows, and real defense-style PDF packet generation.
- **MedForge** — medical image/mechanism teaching workflows, generated visuals, and Blender-backed 3D studio paths.
- **GrimForge** — full-episode creative pipeline with explicit **3D / 2.5D / 2D** routes, narration, captions, and MP4 assembly.
- **Forge Learn** — synchronized teaching companion covering shipping capabilities and failure modes.

**Current status:** implementation candidate. Automated structural/fixture gates pass. A repeatable [live acceptance runbook](forge-suite/current/LIVE_ACCEPTANCE_RUNBOOK.md) now defines the evidence and thresholds for Blender/ComfyUI visual quality, narrator quality, and Windows target-PC behavior; those live gates remain pending until real runs meet the published criteria.

See [Forge Suite current source](forge-suite/current/), [acceptance status](forge-suite/current/ACCEPTANCE_STATUS.md), [live acceptance runbook](forge-suite/current/LIVE_ACCEPTANCE_RUNBOOK.md), and [product blueprint](forge-suite/current/PRODUCT_COMPLETION_BLUEPRINT.md).

Older Elias, Evidence Auditor, and GrimForge folders remain in the repository as development history.
<!-- FORGE-SUITE-CURRENT:END -->

## Featured app — Elias Evidence Auditor Pro

**▶ Test the current production app:** https://elias-evidence-assistant-simscb.v2.appdeploy.ai/

**Current app entry point:** [`portfolio/evidence-auditor/00_CURRENT_APP/`](portfolio/evidence-auditor/00_CURRENT_APP/)

Elias is the newest Evidence Auditor build: a signed-in, source-grounded workspace with large-PDF indexing, OCR and multimodal intake, floating one-click Copilot actions, VA Law & Rater Lens, case review, voice, web research, and packet drafting. The older Streamlit implementation is preserved under `portfolio/evidence-auditor/legacy-streamlit/` so the current build is no longer buried among legacy modules.

**A privacy-first, evidence-grounded AI advocate for medical complexity, veterans, disability
benefits, and accommodations.**

ServiceBridge helps a claimant or authorized advocate turn a difficult record into a traceable
timeline, evidence map, question list, and careful draft. It was shaped by years of lived
experience navigating fragmented medical care, National Guard service records, VA claims,
disability programs, and inaccessible administrative systems.

This is an early proprietary foundation—not a medical device, law firm, accredited veterans'
representative, or benefits decision-maker.

## Why this project exists

Complex cases are rarely defeated by a lack of effort. They are defeated by fragmentation:

- a medical fact gets separated from its source;
- a claimant report is mistakenly restated as a physician's conclusion;
- a Guard member's entire career is reduced to one automated “active duty” date range;
- VA service connection, VA rating, SSDI, state disability, and ADA standards get blended;
- cognitive or neurological symptoms make forms and deadlines harder precisely when precision
  matters most;
- an external letter volunteers irrelevant facts or speculative arguments that the record never
  required.

ServiceBridge is designed to reduce that burden while keeping the human claimant in control.

## What it does today

- Ingests TXT, Markdown, JSON, PDF, and DOCX records into a local SQLite evidence index.
- Records source type, title, hash, date, author, location, and evidence class.
- Redacts common high-risk identifiers before indexing by default.
- Retrieves relevant excerpts with stable source IDs and locators.
- Builds grounded prompt bundles without sending data anywhere (`prompt` mode is the default).
- Optionally calls the OpenAI Responses API only when the operator explicitly chooses it.
- Applies distinct reasoning rules for:
  - VA service connection, including Guard/Reserve duty-status verification;
  - VA ratings;
  - TDIU and SMC;
  - SSDI/SSI;
  - state disability programs;
  - student-loan total and permanent disability processes;
  - ADA/Section 504 accommodations; and
  - clinical appointment advocacy.
- Separates private case analysis from material intended for an outside recipient.

## The evidence contract

Every substantive answer is instructed to keep these categories separate:

| Category | Meaning |
|---|---|
| Records prove | Directly supported by a cited source |
| Claimant/witness reports | A report that must not be relabeled as an objective finding |
| Evidence suggests | A bounded inference, clearly labeled |
| Unknown or missing | A gap that cannot be filled by confident prose |

Original records, signed opinions, agency decisions, and current governing law always control.

## Quick start

Python 3.11 or later is required.

```bash
git clone https://github.com/ajkivela369-coder/servicebridge-advocate.git
cd servicebridge-advocate
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[all]"
```

Create a local evidence index and add records:

```bash
servicebridge init
servicebridge ingest ./private_data/orders.pdf --class official_record --date 2021-10-24
servicebridge ingest ./private_data/clinic-note.pdf --class clinical_record
servicebridge sources
```

Build a fully local, inspectable prompt bundle:

```bash
servicebridge ask \
  "What evidence supports reliable-attendance limitations?" \
  --lane ssdi_ssi \
  --mode private_analysis
```

To intentionally use an OpenAI model:

```bash
export OPENAI_API_KEY="..."
servicebridge ask \
  "Draft a concise accommodation request grounded only in the retrieved records." \
  --lane ada_504 \
  --mode external_draft \
  --audience "university disability office" \
  --output "email" \
  --provider openai
```

The integration uses the current
[Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
and requests `store=False`. Operators remain responsible for reviewing their organization's
data-use, retention, and regulated-data requirements before transmitting any record.

## Local API

```bash
uvicorn servicebridge.api:app --reload
```

`POST /v1/ask` defaults to prompt-only mode. API documentation is available locally at `/docs`.
Do not expose this development server to the internet or use it as a production PHI service.

## Privacy by design

Real case material belongs in `private_data/`, `records/`, `case_files/`, or `uploads/`. All are
ignored by Git. Extracted text, OCR, databases, and exports are ignored too. The repository
contains fictional demonstration records only.

Automated redaction is a backstop, **not proof of de-identification**. Names, rare diagnoses,
dates, locations, military units, and narrative combinations may still identify someone. Human
review is mandatory before sharing or committing any output.

Read [PRIVACY.md](PRIVACY.md) before using real records and [SAFETY.md](SAFETY.md) before relying
on any generated result.

## What “specialized model” means here

The project currently uses domain policy, retrieval-augmented generation, source provenance,
and evaluation rules around a general model. It does **not** train model weights on a claimant's
private record. That is deliberate: this approach is easier to inspect, update, correct, and keep
private. Fine-tuning may eventually help with format and style, but it must never be used as a
substitute for source retrieval or current-law verification.

## Intellectual property & organizational flexibility

ServiceBridge Advocate is an early-stage technology and social-impact venture. Its products,
business model, organizational structure, policies, pricing, partnerships, technical architecture,
and funding strategy may evolve as the project develops.

Current proprietary materials are governed by the repository LICENSE. Third-party components remain governed by their own licenses; earlier versions validly distributed under prior licenses remain subject to those prior terms.
It does not, by itself, grant rights to ServiceBridge trademarks, branding, unpublished
confidential know-how, future proprietary components, datasets, or patent rights beyond what
applicable law and the license provide.

ServiceBridge may seek appropriate protection for qualifying intellectual property through
trademarks, copyrights, patents where applicable, trade-secret practices, licensing terms, and
other lawful mechanisms. The venture also retains flexibility to operate through or form an LLC,
corporation, public-benefit entity, affiliated nonprofit, subsidiary, partnership, or other suitable
structure and to pursue commercial, grant-funded, philanthropic, government-contracting,
research, licensing, or investment opportunities.

See [Intellectual Property & Organizational Flexibility](docs/INTELLECTUAL_PROPERTY_AND_ORGANIZATIONAL_FLEXIBILITY.md)
for the fuller project statement.

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check src tests
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/BENEFIT_LANES.md](docs/BENEFIT_LANES.md), and [ROADMAP.md](ROADMAP.md).

## License

Proprietary — all rights reserved. See [LICENSE](LICENSE).