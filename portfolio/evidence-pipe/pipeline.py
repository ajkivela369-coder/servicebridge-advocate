"""EvidencePipe: privacy-safe ETL learning lab.

Uses only Python standard library so it can run inside the existing ServiceBridge repository.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_FIELDS = ("record_id", "source_type", "title", "date", "text")


@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    source_type: str
    title: str
    date: str
    text: str
    source_locator: str
    fingerprint: str


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_date(value: str) -> str:
    """Normalize a small, explicit set of date formats to ISO YYYY-MM-DD.

    Raises ValueError rather than guessing when the format is unsupported.
    """
    value = value.strip()
    formats = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unsupported date format: {value!r}")


def stable_fingerprint(record: dict[str, str]) -> str:
    payload = "|".join(
        [
            record["source_type"].lower(),
            record["title"].lower(),
            record["date"],
            normalize_whitespace(record["text"]).lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def transform(raw: dict) -> EvidenceRecord:
    missing = [field for field in REQUIRED_FIELDS if not raw.get(field)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    clean = {
        "record_id": normalize_whitespace(str(raw["record_id"])),
        "source_type": normalize_whitespace(str(raw["source_type"])).lower(),
        "title": normalize_whitespace(str(raw["title"])),
        "date": normalize_date(str(raw["date"])),
        "text": normalize_whitespace(str(raw["text"])),
        "source_locator": normalize_whitespace(str(raw.get("source_locator", "unknown"))),
    }
    return EvidenceRecord(
        **clean,
        fingerprint=stable_fingerprint(clean),
    )


def extract_jsonl(path: Path) -> Iterable[tuple[int, dict]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            yield line_number, json.loads(line)


def run_pipeline(path: Path) -> dict:
    valid: list[EvidenceRecord] = []
    quarantined: list[dict] = []
    seen: set[str] = set()
    duplicates: list[dict] = []

    for line_number, raw in extract_jsonl(path):
        try:
            record = transform(raw)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            quarantined.append({"line": line_number, "error": str(exc), "raw": raw})
            continue

        if record.fingerprint in seen:
            duplicates.append(
                {"line": line_number, "record_id": record.record_id, "fingerprint": record.fingerprint}
            )
            continue

        seen.add(record.fingerprint)
        valid.append(record)

    return {
        "valid_records": [asdict(record) for record in valid],
        "quarantined": quarantined,
        "duplicates": duplicates,
        "summary": {
            "valid": len(valid),
            "quarantined": len(quarantined),
            "duplicates": len(duplicates),
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python pipeline.py <records.jsonl>")
        return 2

    result = run_pipeline(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
