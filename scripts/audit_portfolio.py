#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "portfolio"

CATALOG = {
    "NeuroEval": "handshake-neuroeval",
    "HealthQA Auditor": "meridial-healthqa",
    "Evidence Auditor Pro": "evidence-auditor",
    "PairRank": "pairrank",
    "CiteGuard": "citeguard",
    "RaterLab": "raterlab",
    "Benchmark Forge": "benchmark-forge",
    "GrimForge Studio": "grimforge-studio",
    "StudyForge": "studyforge",
    "WildTake Studio": "wildtake-studio",
    "CareFlow Research Lab": "careflow-research-lab",
}

errors: list[str] = []
checks: list[str] = []

def require(condition: bool, message: str) -> None:
    if condition:
        checks.append(message)
    else:
        errors.append(message)

portfolio_readme = PORTFOLIO / "README.md"
require(portfolio_readme.is_file(), "portfolio/README.md exists")
text = portfolio_readme.read_text(encoding="utf-8") if portfolio_readme.is_file() else ""

for name, rel in CATALOG.items():
    folder = PORTFOLIO / rel
    require(folder.is_dir(), f"{name}: directory exists")
    readme = folder / "README.md"
    require(readme.is_file(), f"{name}: README exists")
    if readme.is_file():
        body = readme.read_text(encoding="utf-8", errors="replace")
        require(len(body.strip()) >= 120, f"{name}: README has substantive content")

# Catalog synchronization: every QC app should be visible in the portfolio README.
for name in CATALOG:
    require(name.lower() in text.lower(), f"{name}: listed in portfolio catalog")

# Verify local Markdown links from the portfolio catalog.
for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
    target = target.strip()
    if not target or "://" in target or target.startswith("#") or target.startswith("mailto:"):
        continue
    path = (PORTFOLIO / target.split("#", 1)[0]).resolve()
    require(path.exists(), f"portfolio README local link exists: {target}")

# CareFlow has additional recruiter-facing and safety/provenance requirements.
careflow = PORTFOLIO / "careflow-research-lab" / "index.html"
require(careflow.is_file(), "CareFlow: self-contained app exists")
if careflow.is_file():
    body = careflow.read_text(encoding="utf-8", errors="replace")
    required_markers = [
        '<html lang="en">',
        'name="viewport"',
        "Independent portfolio study",
        "Demo data · No PHI",
        "Research Brief",
        "Participants",
        "Study Room",
        "Notes",
        "Synthesis",
        "Findings",
        "Repository",
        "Case Study",
        "simulated",
        "Researcher interpretation",
    ]
    for marker in required_markers:
        require(marker.lower() in body.lower(), f"CareFlow marker present: {marker}")
    require('src="app.js"' not in body and 'href="styles.css"' not in body,
            "CareFlow: committed demo is self-contained")

# Portfolio claims must preserve provenance and avoid representing independent work as employment.
require("not claims of paid ai employment" in text.lower(),
        "portfolio provenance: independent projects are not represented as paid AI employment")

root_readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace")
require("implementation candidate" in root_readme.lower(),
        "Forge: README preserves implementation-candidate boundary")
require("require target-pc acceptance" in root_readme.lower(),
        "Forge: README preserves pending live-validation boundary")

# Common accidental-private-artifact paths should never be committed to this public portfolio.
for forbidden in ("private_data", "records", "case_files", "uploads"):
    path = ROOT / forbidden
    require(not path.exists(), f"public repo: forbidden private path absent: {forbidden}")

if errors:
    print("PORTFOLIO QUALITY AUDIT: FAIL")
    for item in errors:
        print("FAIL:", item)
    print(f"{len(checks)} checks passed; {len(errors)} failed")
    raise SystemExit(1)

print("PORTFOLIO QUALITY AUDIT: PASS")
print(f"{len(checks)} checks passed; 0 failed")
