"""Repository-level smoke checks for every portfolio application.

These checks are intentionally lightweight: they validate that each app exists,
contains a meaningful entry file, and that all Python/JSON files in the portfolio
parse cleanly. This keeps CI deterministic without depending on live services or
browser automation.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "portfolio"

EXPECTED_APPS = {
    "aj-job-fisher": "package.json",
    "benchmark-forge": "dashboard.py",
    "citeguard": "dashboard.py",
    "evidence-auditor": "README.md",
    "grimforge-studio": "engine.py",
    "handshake-neuroeval": "pyproject.toml",
    "meridial-healthqa": "pyproject.toml",
    "pairrank": "dashboard.py",
    "raterlab": "dashboard.py",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    check(PORTFOLIO.is_dir(), "portfolio directory is missing")

    for app, entry in EXPECTED_APPS.items():
        app_dir = PORTFOLIO / app
        check(app_dir.is_dir(), f"missing portfolio app: {app}")
        check((app_dir / entry).is_file(), f"{app}: missing required entry {entry}")

    python_files = sorted(PORTFOLIO.rglob("*.py"))
    check(python_files, "no Python files found under portfolio")
    for path in python_files:
        text = path.read_text(encoding="utf-8")
        try:
            ast.parse(text, filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise AssertionError(f"invalid Python syntax in {path}: {exc}") from exc

    json_files = sorted(PORTFOLIO.rglob("*.json"))
    for path in json_files:
        text = path.read_text(encoding="utf-8")
        try:
            json.loads(text)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise AssertionError(f"invalid JSON in {path}: {exc}") from exc

    job_fisher_package = PORTFOLIO / "aj-job-fisher" / "package.json"
    package = json.loads(job_fisher_package.read_text(encoding="utf-8"))
    check(package.get("scripts", {}).get("build"), "Job Fisher package.json is missing a build script")
    check(package.get("dependencies", {}).get("react"), "Job Fisher package.json is missing React")

    print(f"portfolio smoke checks passed ({len(EXPECTED_APPS)} apps, {len(python_files)} Python files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
