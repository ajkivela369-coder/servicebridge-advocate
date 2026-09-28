from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


def document_capabilities() -> dict[str, bool]:
    return {
        "pypdf": importlib.util.find_spec("pypdf") is not None,
        "paddleocr": importlib.util.find_spec("paddleocr") is not None,
    }


def extract_pdf_text(path: str | Path) -> list[dict[str, Any]]:
    """Extract embedded PDF text locally with pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Local PDF text extraction requires pypdf. "
            "Install servicebridge-advocate[documents]."
        ) from exc

    path = Path(path)
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(
            {
                "page": index,
                "text": text,
                "needs_ocr": len(text.strip()) < 20,
            }
        )
    return pages


def paddle_ocr(path: str | Path, *, engine: str = "paddle") -> dict[str, Any]:
    """
    Run PaddleOCR locally using the current PaddleOCR.predict API.

    PaddleOCR may download model weights on first use unless they have already
    been installed/cached locally. For true offline use, provision the model
    files before switching the machine offline.
    """
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("PaddleOCR is not installed.") from exc

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        engine=engine,
    )
    results = ocr.predict(str(Path(path)))

    raw_results = []
    text_parts: list[str] = []
    for result in results:
        payload = getattr(result, "json", None)
        if callable(payload):
            payload = payload()
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {"raw": payload}
        if payload is None:
            payload = {}
        raw_results.append(payload)
        text_parts.extend(_collect_text(payload))

    return {
        "engine": "PaddleOCR",
        "source": str(Path(path)),
        "text": "\n".join(x for x in text_parts if x).strip(),
        "results": raw_results,
    }


def _collect_text(value: Any) -> list[str]:
    """Best-effort extraction from PaddleOCR result JSON without discarding raw output."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if key_lower in {"rec_text", "text", "markdown_text"} and isinstance(item, str):
                found.append(item)
            elif key_lower in {"rec_texts", "texts", "markdown_texts"} and isinstance(item, list):
                found.extend(str(x) for x in item if isinstance(x, (str, int, float)))
            else:
                found.extend(_collect_text(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_collect_text(item))
    return found
