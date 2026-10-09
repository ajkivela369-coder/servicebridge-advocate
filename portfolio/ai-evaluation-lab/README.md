# AJ AI Evaluation Lab — v2.0.0

Four browser-only review workflows with Simple and Pro modes, guided examples, explicit actions, human review, readable reports, print/PDF, and Pro JSON export.

| Tool | Use it to | First run |
| --- | --- | --- |
| [NeuroEval](https://ai-evaluation-lab-eta.vercel.app/neuroeval) | Review neuroscience explanations for expected concept mentions and wording signals | Choose a topic → try its example → review the answer → verify against a source |
| [HealthQA Auditor](https://ai-evaluation-lab-eta.vercel.app/healthqa) | Audit health-content wording for review signals | Load a scenario → audit the content → inspect flagged excerpts → record a decision |
| [PairRank](https://ai-evaluation-lab-eta.vercel.app/pairrank) | Compare two answers using human ratings and a written rationale | Enter a shared task and two answers → rate both → compare → explain the preference |
| [CiteGuard](https://ai-evaluation-lab-eta.vercel.app/citeguard) | Find lexical source-match candidates and record actual support separately | Add claims → add `SOURCE_ID | excerpt` lines → find matches → read sources and record support |

NeuroEval includes synaptic transmission, action potentials, learning/plasticity, myelin, autonomic regulation, the neuromuscular junction, EEG/fMRI, sleep/circadian rhythms, and Other / my own topic. Each educational topic has its own prompt, expected concepts, example, review focus, and an external reference for independent reading. Reference links are not automatically fetched or verified.

Simple is the default. Pro adds review context, PairRank importance weights, CiteGuard overlap thresholds, JSON export, and inspectable output. The floating Elias guide answers built-in usage questions; no AI model is connected, and it does not generate scientific/medical answers.

## Honest result boundaries

- NeuroEval measures phrase mentions, not factual accuracy or semantic understanding. Explicit aliases use `|`.
- HealthQA detects configured wording patterns. Even no-pattern results require human review; no medical safety certification is produced.
- PairRank computes human-supplied ratings. Blank ratings and all-zero weights cannot produce a valid comparison. It never invents a rationale for arbitrary text.
- CiteGuard labels lexical matches as candidates, never automatically supported claims. Source-support decisions are separate human judgments. High overlap can coexist with direct contradiction.
- Examples are original educational/synthetic teaching material. PairRank example ratings are explicitly illustrative.

## Run locally

Requires Node 18+ for tests and any static HTTP server for the app. There are no third-party runtime dependencies.

```bash
npm test
python -m http.server 8080
```

Open `/neuroeval/`, `/healthqa/`, `/pairrank/`, or `/citeguard/` on the local server. Vercel clean URLs serve the public paths without trailing slashes.

## Privacy and export

Inputs stay in tab session storage so drafts survive refresh. No user text is submitted to a model service or backend; source URLs are not fetched. Clear inputs removes this tool's current saved draft. Each export contains current inputs, method boundaries, review results, and human notes. Readable reports include all detected excerpts even when screen disclosures are collapsed. Print / Save PDF uses the browser's normal print dialog.

## Source provenance

This directory is the maintained static source for the shared Vercel deployment. It extends the browser implementation originally located at `C:\Users\user\Forge\ai-evaluation-lab`; the earlier Python projects under `handshake-neuroeval`, `meridial-healthqa`, `pairrank`, and `citeguard` remain project history.

Independent research and portfolio work by Alexander J. Kivela. No paid employment or clinical system claims are made.
