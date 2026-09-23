"""Lossless assembly and structural QA for user-selected evidence PDF pages."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader, PdfWriter


@dataclass
class PacketItem:
    path: Path
    pages: list[int]
    label: str
    kind: str
    citation: str = ""


def load_manifest(path: Path) -> tuple[list[PacketItem], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for entry in data.get("items", []):
        source = (path.parent / entry["path"]).resolve()
        pages = entry.get("pages", [])
        if not pages or any(type(page) is not int or page < 1 for page in pages):
            raise ValueError(f"{source.name}: pages must be positive one-based integers")
        kind = entry.get("kind", "record")
        if kind not in {"record", "diagram", "screenshot", "law"}:
            raise ValueError(f"{source.name}: invalid kind {kind}")
        if kind == "law" and not entry.get("citation"):
            raise ValueError(f"{source.name}: law pages need a citation and jurisdiction")
        items.append(PacketItem(source, pages, entry.get("label", source.name), kind, entry.get("citation", "")))
    if not items:
        raise ValueError("Manifest has no items")
    return items, data


def inspect_packet(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, 1):
        links = []
        for ref in page.get("/Annots", []):
            annotation = ref.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                url = str(action["/URI"])
                links.append({"url": url, "valid_scheme": urlparse(url).scheme in {"https", "http"}})
        pages.append({"page": number, "text_chars": len(page.extract_text() or ""), "images": len(page.images), "links": links})
    return {"file": str(path), "bytes": path.stat().st_size, "pages": pages,
            "page_count": len(pages), "link_count": sum(len(p["links"]) for p in pages),
            "image_pages": sum(bool(p["images"]) for p in pages),
            "textless_pages": [p["page"] for p in pages if p["text_chars"] < 20]}


def assemble(manifest: Path, output: Path, max_mb: float = 5) -> dict:
    items, data = load_manifest(manifest)
    writer = PdfWriter()
    index = []
    for item in items:
        if not item.path.is_file():
            raise FileNotFoundError(item.path)
        reader = PdfReader(str(item.path))
        if reader.is_encrypted:
            raise ValueError(f"Encrypted PDF: {item.path}")
        if max(item.pages) > len(reader.pages):
            raise ValueError(f"{item.path.name}: page outside 1-{len(reader.pages)}")
        start = len(writer.pages) + 1
        for page_number in item.pages:
            writer.add_page(reader.pages[page_number - 1])
        writer.add_outline_item(item.label, start - 1)
        index.append({"label": item.label, "kind": item.kind, "citation": item.citation,
                      "source": item.path.name, "source_pages": item.pages, "packet_pages": list(range(start, start + len(item.pages)))})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)
    report = inspect_packet(output)
    report["index"] = index
    report["jurisdiction"] = data.get("jurisdiction", "unspecified")
    report["under_limit"] = report["bytes"] < max_mb * 1024 * 1024
    report["max_mb"] = max_mb
    report["ready"] = report["under_limit"] and all(
        link["valid_scheme"] for page in report["pages"] for link in page["links"]
    )
    report["notes"] = ["Visual pages are preserved as supplied; inspect diagrams and screenshots manually.",
                       "Law citations are supplied by the author; currentness and applicability require review."]
    return report
