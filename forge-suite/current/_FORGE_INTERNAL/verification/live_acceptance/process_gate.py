from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

required = {
    ROOT / "LIVE_ACCEPTANCE_RUNBOOK.md": [
        "Live-engine-tested",
        "Human-reviewed",
        "Blender / ComfyUI visual quality",
        "Narrator quality",
        "Windows target-PC behavior",
        "CareFlow real-participant UX research",
        "zero critical defects",
    ],
    ROOT / "_FORGE_INTERNAL/verification/live_acceptance/VISUAL_QUALITY_RUBRIC.md": [
        "mean score >= 4.0",
        "zero critical defects",
        "Continuity",
    ],
    ROOT / "_FORGE_INTERNAL/verification/live_acceptance/NARRATOR_QUALITY_RUBRIC.md": [
        "overall mean >= 4.0",
        "intelligibility >= 4",
        "naturalness >= 4",
    ],
    ROOT / "_FORGE_INTERNAL/verification/live_acceptance/windows_acceptance.ps1": [
        "Get-FileHash",
        "ForgeHome",
        'ValidateSet("before","after")',
    ],
    ROOT.parents[1] / "portfolio/careflow-research-lab/REAL_PARTICIPANT_STUDY_PROTOCOL.md": [
        "No PHI",
        "Observation",
        "Interpretation",
        "Contradictory",
    ],
}

failures = []
passed = []
for path, markers in required.items():
    if not path.exists():
        failures.append(f"missing: {path}")
        continue
    body = path.read_text(encoding="utf-8", errors="replace")
    for marker in markers:
        if marker.lower() not in body.lower():
            failures.append(f"{path.name}: missing marker {marker!r}")
        else:
            passed.append(f"{path.name}: {marker}")

if failures:
    print("LIVE ACCEPTANCE PROCESS GATE: FAIL")
    for item in failures:
        print("FAIL:", item)
    raise SystemExit(1)

print("LIVE ACCEPTANCE PROCESS GATE: PASS")
print(f"{len(passed)} required controls present")
