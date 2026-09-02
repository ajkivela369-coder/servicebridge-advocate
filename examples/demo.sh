#!/usr/bin/env bash
set -euo pipefail

demo_db="${TMPDIR:-/tmp}/servicebridge-demo.sqlite3"
servicebridge --db "$demo_db" init
servicebridge --db "$demo_db" ingest examples/synthetic_case/clinic_note.txt --class clinical_record
servicebridge --db "$demo_db" ingest examples/synthetic_case/employer_statement.txt --class correspondence
servicebridge --db "$demo_db" ask \
  "What evidence addresses reliable attendance and sustained work?" \
  --lane ssdi_ssi \
  --mode private_analysis
