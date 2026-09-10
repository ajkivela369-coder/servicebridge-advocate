from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from neuroeval import evaluate

DATA = Path(__file__).parent / "data" / "benchmark_extended.jsonl"

def bucket(score: int) -> str:
    if score >= 80:
        return "PASS"
    if score >= 60:
        return "REVIEW"
    return "FAIL"

rows = [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]
truth, pred = [], []
for row in rows:
    result = evaluate(row["answer"], row.get("required_concepts", []))
    truth.append(row["expected"])
    pred.append(bucket(result.total))

labels = ["PASS", "REVIEW", "FAIL"]
matrix = {t: Counter() for t in labels}
for t, p in zip(truth, pred):
    matrix[t][p] += 1

correct = sum(t == p for t, p in zip(truth, pred))
print(f"cases={len(rows)} accuracy={correct/len(rows):.3f}")
print("confusion_matrix")
print("truth\\pred," + ",".join(labels))
for t in labels:
    print(t + "," + ",".join(str(matrix[t][p]) for p in labels))
