from __future__ import annotations

import json
from typing import Any


def default_memory() -> dict[str, Any]:
    return {
        "enabled": True,
        "case_label": "",
        "goal": "",
        "notes": "",
        "auto_summary": "No case record loaded yet.",
    }


def summarize_workspace(result: dict, sources: list[dict]) -> str:
    if not sources or not result:
        return "No case record loaded yet."
    issues = sorted(
        (result.get("issue_summary") or {}).items(),
        key=lambda pair: (-pair[1], pair[0]),
    )[:5]
    issue_text = ", ".join(name.replace("_", " ") for name, _ in issues) or "no issue groups detected"
    return (
        f"Loaded record: {len(sources)} source/page units; {len(result.get('items', []))} evidence passages; "
        f"top issue groups: {issue_text}; {len(result.get('potential_contradictions', []))} tension candidate(s); "
        f"{len(result.get('missing_record_flags', []))} record-gap signal(s)."
    )


def memory_context(memory: dict) -> str:
    if not memory or not memory.get("enabled", True):
        return ""
    parts = []
    if memory.get("case_label"):
        parts.append(f"Case: {memory['case_label']}")
    if memory.get("goal"):
        parts.append(f"Goal: {memory['goal']}")
    if memory.get("notes"):
        parts.append(f"Notes: {memory['notes']}")
    if memory.get("auto_summary"):
        parts.append(memory["auto_summary"])
    return " | ".join(parts)


def export_memory(memory: dict) -> str:
    safe = dict(memory or {})
    safe.pop("raw_documents", None)
    return json.dumps(safe, indent=2, ensure_ascii=False)


def import_memory(text: str) -> dict:
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Memory file must contain a JSON object.")
    merged = default_memory()
    for key in merged:
        if key in parsed:
            merged[key] = parsed[key]
    merged["enabled"] = bool(merged.get("enabled", True))
    return merged
