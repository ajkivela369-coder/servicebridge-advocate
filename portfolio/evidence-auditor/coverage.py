from __future__ import annotations

from collections import defaultdict
from typing import Sequence


def assess_issue_coverage(items: Sequence[dict]) -> dict:
    """Summarize issue coverage, provenance depth, and source diversity.

    This is a reviewer-routing aid. It does not decide whether an issue is legally
    sufficient or medically established.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        for issue in item.get("issues", []) or ["general_evidence"]:
            grouped[str(issue)].append(item)

    issues = []
    for issue, evidence in sorted(grouped.items()):
        source_names = {e.get("source_name") for e in evidence if e.get("source_name")}
        source_types = {e.get("source_type") for e in evidence if e.get("source_type") and e.get("source_type") != "unspecified"}
        pages = {(e.get("source_name"), e.get("page")) for e in evidence if e.get("page") is not None}
        favorable = sum(e.get("stance") == "favorable" for e in evidence)
        unfavorable = sum(e.get("stance") == "unfavorable" for e in evidence)
        mixed = sum(e.get("stance") == "mixed" for e in evidence)

        depth = len(evidence)
        diversity = len(source_types)
        locatable = len(pages)
        score = min(100, depth * 14 + diversity * 14 + min(locatable, 3) * 8)

        flags: list[str] = []
        if depth < 2:
            flags.append("Only one evidence passage is mapped to this issue.")
        if len(source_names) < 2:
            flags.append("Issue currently depends on a single named source.")
        if diversity < 2:
            flags.append("Source-type diversity is limited.")
        if locatable == 0:
            flags.append("No page-locatable PDF evidence is mapped to this issue.")
        if favorable and unfavorable:
            flags.append("Opposing evidence exists and should be reconciled.")

        band = "strong" if score >= 75 else "developing" if score >= 45 else "thin"
        issues.append({
            "issue": issue,
            "coverage_score": score,
            "coverage_band": band,
            # Backward-compatible alias used by packet/report consumers. Keeping both keys
            # prevents a developing/strong issue from silently rendering as the default thin band.
            "band": band,
            "passages": depth,
            "named_sources": len(source_names),
            "source_types": sorted(source_types),
            "page_locators": locatable,
            "favorable": favorable,
            "unfavorable": unfavorable,
            "mixed": mixed,
            "flags": flags,
        })

    thin = [i for i in issues if i["coverage_band"] == "thin"]
    developing = [i for i in issues if i["coverage_band"] == "developing"]
    strong = [i for i in issues if i["coverage_band"] == "strong"]
    return {
        "issue_count": len(issues),
        "strong": len(strong),
        "developing": len(developing),
        "thin": len(thin),
        "issues": issues,
        "priority_gaps": sorted(
            [i for i in issues if i["flags"]],
            key=lambda i: (i["coverage_score"], -len(i["flags"]), i["issue"]),
        ),
        "note": "Coverage scores measure review depth and provenance diversity, not claim merit or legal sufficiency.",
    }
