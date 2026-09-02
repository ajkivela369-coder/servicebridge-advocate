# ServiceBridge Advocate

**A privacy-first, evidence-grounded AI advocate for medical complexity, veterans, disability
benefits, and accommodations.**

ServiceBridge helps a claimant or authorized advocate turn a difficult record into a traceable
timeline, evidence map, question list, and careful draft. It was shaped by years of lived
experience navigating fragmented medical care, National Guard service records, VA claims,
disability programs, and inaccessible administrative systems.

This is an early, open-source foundation—not a medical device, law firm, accredited veterans'
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
git clone https://github.com/YOUR-ACCOUNT/servicebridge-advocate.git
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

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check src tests
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/BENEFIT_LANES.md](docs/BENEFIT_LANES.md), and [ROADMAP.md](ROADMAP.md).

## License

MIT License. See [LICENSE](LICENSE).