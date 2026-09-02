#!/usr/bin/env python3
"""Fail CI when common secrets or private-data paths appear in the repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRECTORIES = {"private_data", "records", "case_files", "uploads", "artifacts", "exports"}
SKIP_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"}
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".toml", ".yml", ".yaml", ".json", ".example", ".sh", ".gitignore"
}
PATTERNS = {
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Social Security number": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
}
ALLOWLIST = {
    ("tests/test_redaction.py", "Social Security number"),
}


def iter_files():
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in SKIP_DIRECTORIES for part in relative.parts):
            continue
        if path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore"):
            yield path, relative


def main() -> int:
    problems: list[str] = []
    for path in ROOT.iterdir():
        if path.is_dir() and path.name in FORBIDDEN_DIRECTORIES:
            problems.append(f"forbidden private-data directory present: {path.name}/")

    for path, relative in iter_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text) and (str(relative), label) not in ALLOWLIST:
                problems.append(f"possible {label}: {relative}")

    if problems:
        print("Public-repository safety check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("Public-repository safety check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
