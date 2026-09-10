from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from healthqa import audit

DATA = Path(__file__).parent / "data" / "benchmark_extended.jsonl"
rows = [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]
labels = ["PASS", "REVIEW", "ESCALATE"]
truth, pred = [], []
for row in rows:
    result = audit(row["text"])
    truth.append(row["expected"])
    pred.append(result.disposition)

matrix = {t: Counter() for t in labels}
for t, p in zip(truth, pred):
    matrix[t][p] += 1

correct = sum(t == p for t, p in zip(truth, pred))
print(f"cases={len(rows)} accuracy={correct/len(rows):.3f}")
print("confusion_matrix")
print("truth\\pred," + ",".join(labels))
for t in labels:
    print(t + "," + ",".join(str(matrix[t][p]) for p in labels))
