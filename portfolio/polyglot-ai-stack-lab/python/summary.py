"""Tiny Python component for Polyglot AI Stack Lab."""

from collections import Counter
import json
from pathlib import Path


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def label_counts(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(str(row["expected"]).upper() for row in rows))


if __name__ == "__main__":
    rows = load_jsonl(Path(__file__).parents[1] / "data" / "benchmark.jsonl")
    print(json.dumps({"rows": len(rows), "labels": label_counts(rows)}, indent=2))
