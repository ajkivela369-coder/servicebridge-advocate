# EvidencePipe Lab

EvidencePipe is a privacy-safe learning project that strengthens AJ's hands-on experience with
data engineering while also producing reusable ideas for Elias Evidence Auditor.

It uses only fictional/synthetic records.

## What this project teaches

- ETL: extract, transform, load
- schema validation
- normalization
- duplicate detection
- provenance tracking
- JSON/JSONL handling
- deterministic pipelines
- testable data-quality rules

## Why it connects to Elias

Elias already depends on trustworthy ingestion, source identity, provenance, and retrieval.
EvidencePipe isolates those concepts into a small, inspectable lab so each step can be learned,
tested, and later reused safely in the production evidence pipeline.

## Pipeline

```text
synthetic JSONL
      |
      v
   extract
      |
      v
 normalize dates/text/source fields
      |
      v
 validate required schema
      |
      +----> quarantine invalid rows
      |
      v
 deduplicate by stable fingerprint
      |
      v
 clean evidence records + lineage report
```

## Run

```bash
python portfolio/evidence-pipe/pipeline.py \
  portfolio/evidence-pipe/sample_records.jsonl
```

## What I can explain after working through this

- Why ETL and data analysis are different
- Why schema validation belongs before downstream AI reasoning
- Why provenance must survive transformation
- How deterministic fingerprints help find duplicate records
- Why invalid rows should be quarantined instead of silently repaired

## Portfolio wording

> Built a Python ETL learning pipeline for synthetic health/evidence records with schema
> validation, normalization, deduplication, provenance preservation, quarantine handling,
> and automated tests. The project was designed to transfer data-engineering lessons into
> Elias Evidence Auditor without using private case data.

This is project experience, not paid employment.
