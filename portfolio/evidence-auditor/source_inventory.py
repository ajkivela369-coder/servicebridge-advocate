from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from source_identity import assign_source_ids


def _compact_ranges(pages: list[int]) -> str:
    if not pages:
        return "—"
    pages = sorted(set(pages))
    ranges: list[str] = []
    start = prev = pages[0]
    for page in pages[1:]:
        if page == prev + 1:
            prev = page
            continue
        ranges.append(str(start) if start == prev else f"{start}–{prev}")
        start = prev = page
    ranges.append(str(start) if start == prev else f"{start}–{prev}")
    return ", ".join(ranges)


def build_source_inventory(sources: Sequence[dict]) -> dict:
    """Build a document-level provenance inventory without retaining extra source content.

    The inventory groups rows by stable source ID and reports observed page range, text-bearing
    pages, blank/unextractable rows, and missing page numbers inside the observed range. It is a
    review-readiness aid, not proof that a source is complete or authentic.
    """
    rows = assign_source_ids(sources)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row.get("source_id") or "UNIDENTIFIED"].append(row)

    documents = []
    for source_id, group in groups.items():
        name = group[0].get("source_name") or "Unknown source"
        pages: list[int] = []
        text_pages: list[int] = []
        blank_pages: list[int] = []
        unpaged = 0
        for row in group:
            page = row.get("page")
            if page is None:
                unpaged += 1
                continue
            try:
                page_num = int(page)
            except (TypeError, ValueError):
                unpaged += 1
                continue
            pages.append(page_num)
            if (row.get("text") or "").strip():
                text_pages.append(page_num)
            else:
                blank_pages.append(page_num)

        missing_pages: list[int] = []
        if pages:
            observed = set(pages)
            missing_pages = [p for p in range(min(pages), max(pages) + 1) if p not in observed]

        flags = []
        if blank_pages:
            flags.append(f"{len(blank_pages)} observed page(s) contain no extractable text.")
        if missing_pages:
            flags.append(f"{len(missing_pages)} page number(s) are absent inside the observed range.")
        if unpaged:
            flags.append(f"{unpaged} source unit(s) have no page locator.")

        documents.append({
            "source_id": source_id,
            "source_name": name,
            "observed_pages": len(set(pages)),
            "page_range": _compact_ranges(pages),
            "text_pages": len(set(text_pages)),
            "blank_pages": _compact_ranges(blank_pages),
            "missing_pages": _compact_ranges(missing_pages),
            "unpaged_units": unpaged,
            "flags": flags,
            "status": "review" if flags else "ready",
        })

    documents.sort(key=lambda d: (d["source_name"].lower(), d["source_id"]))
    return {
        "document_count": len(documents),
        "documents_needing_review": sum(1 for d in documents if d["flags"]),
        "documents": documents,
        "note": "Inventory reflects only the source rows supplied to the app. Missing/blank-page signals are provenance review cues, not proof that an original document is incomplete.",
    }
