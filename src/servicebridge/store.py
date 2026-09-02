from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import EvidenceChunk, EvidenceClass, RetrievalHit, SourceDocument


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    evidence_class TEXT NOT NULL,
    document_date TEXT,
    author TEXT,
    page_count INTEGER,
    sha256 TEXT,
    redacted INTEGER NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    locator TEXT,
    evidence_class TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    source_id UNINDEXED,
    text,
    tokenize = 'porter unicode61'
);
"""


class EvidenceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "EvidenceStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def add_document(self, source: SourceDocument, chunks: list[EvidenceChunk]) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM chunks_fts WHERE source_id = ?", (source.source_id,))
            self.connection.execute("DELETE FROM chunks WHERE source_id = ?", (source.source_id,))
            self.connection.execute(
                """
                INSERT INTO sources (
                    source_id, title, path, evidence_class, document_date, author,
                    page_count, sha256, redacted, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    title=excluded.title,
                    path=excluded.path,
                    evidence_class=excluded.evidence_class,
                    document_date=excluded.document_date,
                    author=excluded.author,
                    page_count=excluded.page_count,
                    sha256=excluded.sha256,
                    redacted=excluded.redacted,
                    metadata_json=excluded.metadata_json
                """,
                (
                    source.source_id,
                    source.title,
                    source.path,
                    source.evidence_class.value,
                    source.document_date,
                    source.author,
                    source.page_count,
                    source.sha256,
                    int(source.redacted),
                    json.dumps(source.metadata, sort_keys=True),
                ),
            )
            self.connection.executemany(
                """
                INSERT INTO chunks (chunk_id, source_id, text, ordinal, locator, evidence_class)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.source_id,
                        chunk.text,
                        chunk.ordinal,
                        chunk.locator,
                        chunk.evidence_class.value,
                    )
                    for chunk in chunks
                ],
            )
            self.connection.executemany(
                "INSERT INTO chunks_fts (chunk_id, source_id, text) VALUES (?, ?, ?)",
                [(chunk.chunk_id, chunk.source_id, chunk.text) for chunk in chunks],
            )

    def search(self, query: str, limit: int = 8) -> list[RetrievalHit]:
        if not query.strip():
            return []
        fts_query = _fts_query(query)
        if not fts_query:
            return []
        rows = self.connection.execute(
            """
            SELECT c.*, s.title, bm25(chunks_fts, 1.0) AS rank
            FROM chunks_fts
            JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
            JOIN sources s ON s.source_id = c.source_id
            WHERE chunks_fts MATCH ?
            ORDER BY rank ASC
            LIMIT ?
            """,
            (fts_query, limit),
        ).fetchall()
        return [
            RetrievalHit(
                chunk=EvidenceChunk(
                    chunk_id=row["chunk_id"],
                    source_id=row["source_id"],
                    text=row["text"],
                    ordinal=row["ordinal"],
                    locator=row["locator"],
                    evidence_class=EvidenceClass(row["evidence_class"]),
                ),
                title=row["title"],
                score=float(-row["rank"]),
            )
            for row in rows
        ]

    def list_sources(self) -> list[SourceDocument]:
        rows = self.connection.execute("SELECT * FROM sources ORDER BY title").fetchall()
        return [
            SourceDocument(
                source_id=row["source_id"],
                title=row["title"],
                path=row["path"],
                evidence_class=EvidenceClass(row["evidence_class"]),
                document_date=row["document_date"],
                author=row["author"],
                page_count=row["page_count"],
                sha256=row["sha256"],
                redacted=bool(row["redacted"]),
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]


def _fts_query(text: str) -> str:
    tokens = []
    current = ""
    for char in text.lower():
        if char.isalnum() or char in {"_", "-"}:
            current += char
        elif current:
            tokens.append(current)
            current = ""
    if current:
        tokens.append(current)
    meaningful = [token for token in tokens if len(token) > 1][:24]
    return " OR ".join(f'"{token}"' for token in meaningful)
