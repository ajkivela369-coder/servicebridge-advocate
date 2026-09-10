from __future__ import annotations

import hashlib
from typing import Sequence


def _group_boundary(previous: dict | None, current: dict) -> bool:
    """Return True when a source row appears to begin a new document instance.

    PDF page rows are expected to be contiguous. A filename change or a page-number reset
    starts a new document group. Rows without page numbers are treated as independent units.
    This keeps duplicate filenames distinguishable without storing the original file bytes.
    """
    if previous is None:
        return True
    if (previous.get("source_name") or "") != (current.get("source_name") or ""):
        return True
    prev_page = previous.get("page")
    page = current.get("page")
    if page is None or prev_page is None:
        return True
    try:
        return int(page) <= int(prev_page)
    except (TypeError, ValueError):
        return True


def assign_source_ids(sources: Sequence[dict]) -> list[dict]:
    """Return source rows with short content-derived document IDs attached.

    IDs are deterministic for the currently supplied source rows and contain no raw source text.
    Existing explicit ``source_id`` values are preserved and propagated across immediately
    contiguous pages from the same document instance. The function does not persist, upload,
    or log source content.
    """
    rows = [dict(source) for source in sources]
    if not rows:
        return rows

    groups: list[list[int]] = []
    current_group: list[int] = []
    previous: dict | None = None
    for index, row in enumerate(rows):
        boundary = _group_boundary(previous, row)

        # If an upstream loader supplied a stable source ID on one page, preserve that identity
        # across later contiguous pages of the same document instead of silently minting a second
        # ID for the remainder of the file. A filename change or page reset still starts a new
        # document instance and therefore blocks propagation.
        if not row.get("source_id") and previous and previous.get("source_id") and not boundary:
            row["source_id"] = previous["source_id"]

        if row.get("source_id"):
            if current_group:
                groups.append(current_group)
                current_group = []
            previous = row
            continue

        if boundary:
            if current_group:
                groups.append(current_group)
            current_group = [index]
        else:
            current_group.append(index)
        previous = row
    if current_group:
        groups.append(current_group)

    for group in groups:
        digest = hashlib.sha256()
        for index in group:
            row = rows[index]
            digest.update(str(row.get("source_name") or "Unknown source").encode("utf-8", errors="ignore"))
            digest.update(b"\x00")
            digest.update(str(row.get("page") or "").encode("utf-8", errors="ignore"))
            digest.update(b"\x00")
            digest.update(str(row.get("text") or "").encode("utf-8", errors="ignore"))
            digest.update(b"\x1e")
        source_id = "SRC-" + digest.hexdigest()[:10].upper()
        for index in group:
            rows[index]["source_id"] = source_id

    return rows


def locator(source: dict) -> str:
    """Format a reviewer locator with source ID when available."""
    name = source.get("source_name") or "Unknown source"
    page = source.get("page")
    source_id = source.get("source_id") or ""
    base = f"{name}, p. {page}" if page else name
    return f"{base} · {source_id}" if source_id else base
