from __future__ import annotations

import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "portfolio"

REQUIRED = {
    "vocalforge": ["README.md", "BUILD_AND_UPGRADE.md"],
    "aj-job-fisher": ["README.md", "package.json", "src/App.tsx"],
    "benchmark-forge": ["README.md", "dashboard.py", "requirements.txt"],
    "careflow-research-lab": ["README.md", "index.html"],
    "citeguard": ["README.md", "dashboard.py", "requirements.txt"],
    "evidence-auditor": ["README.md", "00_CURRENT_APP"],
    "grimforge-studio": ["README.md", "appdeploy/package.json", "engine.py"],
    "handshake-neuroeval": ["README.md", "pyproject.toml", "tests/test_evaluator.py"],
    "meridial-healthqa": ["README.md", "pyproject.toml", "tests/test_auditor.py"],
    "pairrank": ["README.md", "dashboard.py", "requirements.txt"],
    "raterlab": ["README.md", "dashboard.py", "requirements.txt"],
    "searchsignal": [
        "README.md",
        "source/pages/_index.tsx",
        "source/endpoints/audit_POST.ts",
        "source/endpoints/audit_POST.schema.ts",
        "interview-build/package.json",
        "interview-build/server.js",
        "interview-build/public/app.js",
        "interview-build/tests/smoke.mjs",
        "interview-build/GEISEL_INTERVIEW_WALKTHROUGH.md",
    ],
    "studyforge": ["README.md", "appdeploy/package.json"],
    "wildtake-studio": ["README.md", "appdeploy/package.json"],
}

MOJIBAKE = ("â€”", "â†’", "ï»¿", "�")


def fail(message: str) -> None:
    raise SystemExit(f"QC FAIL: {message}")


for project, required_paths in REQUIRED.items():
    root = PORTFOLIO / project
    if not root.is_dir():
        fail(f"missing portfolio project: {project}")
    for relative in required_paths:
        if not (root / relative).exists():
            fail(f"{project}: missing {relative}")

for package in PORTFOLIO.rglob("package.json"):
    try:
        json.loads(package.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON in {package.relative_to(ROOT)}: {exc}")

for source in PORTFOLIO.rglob("*.py"):
    try:
        py_compile.compile(str(source), doraise=True)
    except Exception as exc:
        fail(f"Python syntax error in {source.relative_to(ROOT)}: {exc}")

markdown = [ROOT / "README.md", *PORTFOLIO.rglob("*.md")]
for path in markdown:
    text = path.read_text(encoding="utf-8-sig")
    for marker in MOJIBAKE:
        if marker in text:
            fail(f"mojibake marker {marker!r} in {path.relative_to(ROOT)}")

portfolio_index = (PORTFOLIO / "README.md").read_text(encoding="utf-8")
for expected in ("SearchSignal", "CareFlow Research Lab", "AJ Job Fisher", "QUALITY_CONTROL.md"):
    if expected not in portfolio_index:
        fail(f"portfolio index is missing {expected}")

searchsignal = (PORTFOLIO / "searchsignal" / "README.md").read_text(encoding="utf-8")
for phrase in ("Independent portfolio", "Connector-ready", "not affiliated"):
    if phrase.lower() not in searchsignal.lower():
        fail(f"SearchSignal README missing truth-label phrase: {phrase}")

print(f"QC PASS: {len(REQUIRED)} portfolio projects inventoried; manifests parse; Python syntax compiles; README encoding/truth-label checks pass.")
