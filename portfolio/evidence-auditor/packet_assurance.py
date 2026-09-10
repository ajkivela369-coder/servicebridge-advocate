from __future__ import annotations

from typing import Sequence

from coverage import assess_issue_coverage
from packet_guard import audit_packet_quotes
from readiness import assess_provenance_readiness
from source_inventory import build_source_inventory


def assess_packet_assurance(
    items: Sequence[dict],
    sources: Sequence[dict],
    proposed_quotes: Sequence[str] | None = None,
) -> dict:
    """Combine provenance, coverage, quote integrity, and source reconciliation.

    This is a routing and quality-control aid. It does not decide claim merit, legal sufficiency,
    medical causation, rating percentage, or benefits eligibility. Source-inventory cues are kept
    advisory so this addition does not silently change existing assurance-score semantics.
    """
    proposed_quotes = proposed_quotes or []
    provenance = assess_provenance_readiness(sources)
    coverage = assess_issue_coverage(items)
    quotes = audit_packet_quotes(proposed_quotes, sources)
    source_inventory = build_source_inventory(sources)

    quote_score = 100
    if quotes["quote_count"]:
        quote_score = round(100 * quotes["counts"]["verified"] / quotes["quote_count"])

    coverage_scores = [issue["coverage_score"] for issue in coverage["issues"]]
    coverage_score = round(sum(coverage_scores) / len(coverage_scores)) if coverage_scores else 0
    provenance_score = int(provenance.get("score", 0))

    composite = round(provenance_score * 0.4 + coverage_score * 0.35 + quote_score * 0.25)

    blockers: list[str] = []
    if provenance_score < 70:
        blockers.append("Source provenance is not yet strong enough for a high-confidence reviewer handoff.")
    if coverage.get("thin", 0):
        blockers.append(f"{coverage['thin']} issue(s) remain thinly supported or poorly diversified.")
    if quotes.get("unresolved", 0):
        blockers.append(f"{quotes['unresolved']} proposed verbatim quote(s) are unresolved and should not be exported as verified quotations.")

    if blockers or composite < 75:
        band = "needs_review"
    elif composite < 90:
        band = "review_ready"
    else:
        band = "strong_review_ready"

    return {
        "score": composite,
        "band": band,
        "provenance_score": provenance_score,
        "coverage_score": coverage_score,
        "quote_score": quote_score,
        "blockers": blockers,
        "provenance": provenance,
        "coverage": coverage,
        "quotes": quotes,
        "source_inventory": source_inventory,
        "note": (
            "Packet Assurance measures provenance, evidence coverage, quotation integrity, and source reconciliation for reviewer workflow. "
            "Source-reconciliation cues are advisory and do not change the composite score. It is not a legal or medical merits determination."
        ),
    }
