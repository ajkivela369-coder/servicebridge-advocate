from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, target_chars: int = 1800, overlap_chars: int = 250) -> list[str]:
    """Split text into paragraph-aware chunks with bounded overlap."""

    if target_chars < 300:
        raise ValueError("target_chars must be at least 300")
    if overlap_chars < 0 or overlap_chars >= target_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than target_chars")

    text = normalize_whitespace(text)
    if not text:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > target_chars:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        else:
            sentences = [paragraph]

        for unit in sentences:
            proposed = f"{current}\n\n{unit}".strip() if current else unit
            if current and len(proposed) > target_chars:
                chunks.append(current)
                prefix = current[-overlap_chars:] if overlap_chars else ""
                current = f"{prefix}\n\n{unit}".strip()
            else:
                current = proposed

    if current:
        chunks.append(current)
    return chunks
