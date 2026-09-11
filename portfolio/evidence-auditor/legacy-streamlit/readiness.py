from __future__ import annotations

from typing import Sequence


def assess_provenance_readiness(sources: Sequence[dict]) -> dict:
    """Score whether source units are locatable enough for reviewer use.

    This is a provenance-quality signal, not a legal/medical evidence-strength score.
    """
    total = len(sources)
    if total == 0:
        return {
            "score": 0,
            "grade": "Not ready",
            "total_units": 0,
            "named_source_pct": 0,
            "page_locator_pct": 0,
            "usable_text_pct": 0,
            "flags": ["No source units are loaded."],
        }

    named = sum(bool(str(s.get("source_name") or "").strip()) and str(s.get("source_name")).strip() != "Unknown source" for s in sources)
    paged = sum(s.get("page") not in (None, "", 0) for s in sources)
    usable = sum(bool(str(s.get("text") or "").strip()) for s in sources)

    named_pct = round(100 * named / total)
    page_pct = round(100 * paged / total)
    usable_pct = round(100 * usable / total)

    # Page locators carry the most weight because they make later quotation
    # and exhibit verification materially easier for a human reviewer.
    score = round((0.30 * named_pct) + (0.45 * page_pct) + (0.25 * usable_pct))

    if score >= 90:
        grade = "Packet-ready provenance"
    elif score >= 75:
        grade = "Strong, review gaps"
    elif score >= 50:
        grade = "Needs provenance work"
    else:
        grade = "Not packet-ready"

    flags: list[str] = []
    if named_pct < 100:
        flags.append(f"{total - named} source unit(s) lack a reliable source name.")
    if page_pct < 100:
        flags.append(f"{total - paged} source unit(s) lack a page locator.")
    if usable_pct < 100:
        flags.append(f"{total - usable} source unit(s) contain no usable extracted text.")
    if not flags:
        flags.append("All loaded source units have a source name, page locator, and usable text.")

    return {
        "score": score,
        "grade": grade,
        "total_units": total,
        "named_source_pct": named_pct,
        "page_locator_pct": page_pct,
        "usable_text_pct": usable_pct,
        "flags": flags,
    }
