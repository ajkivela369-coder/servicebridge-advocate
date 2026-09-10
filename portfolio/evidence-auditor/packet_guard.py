from __future__ import annotations

from typing import Sequence

from quote_integrity import verify_quote_contextual


def audit_packet_quotes(quotes: Sequence[str], sources: Sequence[dict]) -> dict:
    """Verify proposed packet quotations and calculate export readiness.

    Only normalized-exact source matches count as verified. Similar wording is
    deliberately kept separate so it cannot silently become a verbatim quote.
    """
    results = []
    for index, quote in enumerate(quotes, 1):
        clean = quote.strip().strip('“”"')
        if not clean:
            continue
        check = verify_quote_contextual(clean, sources)
        results.append(
            {
                "quote_id": f"Q-{index:03d}",
                "quote": clean,
                "status": check["status"],
                "confidence": check.get("confidence", 0.0),
                "matches": check.get("matches", []),
                "note": check.get("note", ""),
            }
        )

    counts = {
        "verified": sum(item["status"] == "verified" for item in results),
        "partial": sum(item["status"] == "partial" for item in results),
        "not_found": sum(item["status"] == "not_found" for item in results),
    }
    unresolved = counts["partial"] + counts["not_found"]
    return {
        "quote_count": len(results),
        "counts": counts,
        "unresolved": unresolved,
        "export_ready": unresolved == 0,
        "results": results,
        "policy": (
            "Packet export is quote-integrity ready only when every proposed verbatim "
            "quotation has a normalized-exact source match. Partial matches must be "
            "replaced with source wording or converted to accurate paraphrase."
        ),
    }
