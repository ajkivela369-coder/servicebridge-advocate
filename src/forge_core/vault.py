from __future__ import annotations

from hashlib import sha256
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
import time
from typing import Any


class ForgeVault:
    """
    One immutable source repository shared by every Forge-backed app.

    Originals are addressed by SHA-256. App references are rows in SQLite, not
    duplicate files. Derived assets point back to parent source IDs.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.originals = self.root / "originals"
        self.derived = self.root / "derived"
        self.originals.mkdir(parents=True, exist_ok=True)
        self.derived.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "vault.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                sha256 TEXT UNIQUE NOT NULL,
                original_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                path TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS refs (
                app_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                role TEXT NOT NULL,
                locator TEXT NOT NULL,
                created_at REAL NOT NULL,
                PRIMARY KEY (app_id, source_id, role, locator)
            );
            CREATE TABLE IF NOT EXISTS derived (
                asset_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                source_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                path TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS text_units (
                text_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                page INTEGER,
                locator TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS text_fts USING fts5(
                text_id UNINDEXED,
                source_id UNINDEXED,
                text,
                tokenize = 'porter unicode61'
            );
            CREATE INDEX IF NOT EXISTS idx_refs_source ON refs(source_id);
            CREATE INDEX IF NOT EXISTS idx_derived_source ON derived(source_id);
            CREATE INDEX IF NOT EXISTS idx_text_units_source ON text_units(source_id);
            """
        )

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "ForgeVault":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _digest(data: bytes) -> str:
        return sha256(data).hexdigest()

    def add_bytes(
        self,
        data: bytes,
        *,
        original_name: str,
        mime_type: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        digest = self._digest(data)
        source_id = f"src_{digest[:20]}"
        ext = "".join(Path(original_name).suffixes)[-16:]
        path = self.originals / f"{digest}{ext}"
        if not path.exists():
            path.write_bytes(data)

        mime = mime_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        with self.db:
            self.db.execute(
                """
                INSERT OR IGNORE INTO sources
                (source_id, sha256, original_name, mime_type, size_bytes, path,
                 metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    digest,
                    original_name,
                    mime,
                    len(data),
                    str(path),
                    json.dumps(metadata or {}, sort_keys=True),
                    time.time(),
                ),
            )
        return self.get_source(source_id) or {}

    def add_path(
        self,
        path: str | Path,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(source)
        return self.add_bytes(
            source.read_bytes(),
            original_name=source.name,
            metadata=metadata,
        )

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            "SELECT * FROM sources WHERE source_id=?",
            (source_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "source_id": row["source_id"],
            "sha256": row["sha256"],
            "original_name": row["original_name"],
            "mime_type": row["mime_type"],
            "size_bytes": int(row["size_bytes"]),
            "path": row["path"],
            "metadata": json.loads(row["metadata_json"]),
            "created_at": float(row["created_at"]),
        }

    def reference(
        self,
        app_id: str,
        source_id: str,
        *,
        role: str = "source",
        locator: str = "",
    ) -> None:
        if self.get_source(source_id) is None:
            raise KeyError(source_id)
        with self.db:
            self.db.execute(
                """
                INSERT OR IGNORE INTO refs
                (app_id, source_id, role, locator, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (app_id, source_id, role, locator, time.time()),
            )

    def add_derived(
        self,
        source_id: str,
        data: bytes,
        *,
        kind: str,
        suffix: str = ".bin",
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.get_source(source_id) is None:
            raise KeyError(source_id)
        digest = self._digest(data)
        asset_id = f"drv_{digest[:20]}"
        safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        path = self.derived / f"{digest}{safe_suffix}"
        if not path.exists():
            path.write_bytes(data)
        with self.db:
            self.db.execute(
                """
                INSERT OR REPLACE INTO derived
                (asset_id, sha256, source_id, kind, path, provenance_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    digest,
                    source_id,
                    kind,
                    str(path),
                    json.dumps(provenance or {}, sort_keys=True),
                    time.time(),
                ),
            )
        return {
            "asset_id": asset_id,
            "sha256": digest,
            "source_id": source_id,
            "kind": kind,
            "path": str(path),
            "provenance": provenance or {},
        }


    def index_text_units(
        self,
        source_id: str,
        units: list[dict[str, Any]],
        *,
        replace: bool = True,
    ) -> int:
        if self.get_source(source_id) is None:
            raise KeyError(source_id)
        rows = []
        for index, unit in enumerate(units, start=1):
            text = str(unit.get("text", "") or "").strip()
            if not text:
                continue
            page = unit.get("page")
            locator = str(
                unit.get("locator")
                or (f"p. {page}" if page is not None else f"unit {index}")
            )
            text_id = f"{source_id}:{page if page is not None else index}:{index}"
            rows.append(
                (
                    text_id,
                    source_id,
                    int(page) if page is not None else None,
                    locator,
                    text,
                    json.dumps(unit.get("metadata", {}), sort_keys=True),
                )
            )

        with self.db:
            if replace:
                self.db.execute("DELETE FROM text_fts WHERE source_id=?", (source_id,))
                self.db.execute("DELETE FROM text_units WHERE source_id=?", (source_id,))
            self.db.executemany(
                """
                INSERT OR REPLACE INTO text_units
                (text_id, source_id, page, locator, text, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            self.db.executemany(
                "INSERT INTO text_fts (text_id, source_id, text) VALUES (?, ?, ?)",
                [(row[0], row[1], row[4]) for row in rows],
            )
        return len(rows)

    def search_text(self, query: str, *, limit: int = 12) -> list[dict[str, Any]]:
        terms = [
            token.lower()
            for token in re.findall(r"[A-Za-z0-9_]{2,}", str(query))
        ]
        if not terms:
            return []
        fts_query = " OR ".join(f'"{term}"' for term in terms[:24])
        rows = self.db.execute(
            """
            SELECT u.text_id, u.source_id, u.page, u.locator, u.text,
                   u.metadata_json, s.original_name, s.sha256,
                   bm25(text_fts, 1.0) AS rank
            FROM text_fts
            JOIN text_units u ON u.text_id = text_fts.text_id
            JOIN sources s ON s.source_id = u.source_id
            WHERE text_fts MATCH ?
            ORDER BY rank ASC
            LIMIT ?
            """,
            (fts_query, max(1, int(limit))),
        ).fetchall()
        return [
            {
                "text_id": row["text_id"],
                "source_id": row["source_id"],
                "source_name": row["original_name"],
                "sha256": row["sha256"],
                "page": row["page"],
                "locator": row["locator"],
                "text": row["text"],
                "score": float(-row["rank"]),
                "metadata": json.loads(row["metadata_json"]),
            }
            for row in rows
        ]

    def references_for(self, source_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT * FROM refs WHERE source_id=? ORDER BY app_id, role, locator",
            (source_id,),
        ).fetchall()
        return [
            {
                "app_id": row["app_id"],
                "source_id": row["source_id"],
                "role": row["role"],
                "locator": row["locator"],
            }
            for row in rows
        ]

    def status(self) -> dict[str, Any]:
        source_count = self.db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        ref_count = self.db.execute("SELECT COUNT(*) FROM refs").fetchone()[0]
        derived_count = self.db.execute("SELECT COUNT(*) FROM derived").fetchone()[0]
        text_unit_count = self.db.execute("SELECT COUNT(*) FROM text_units").fetchone()[0]
        unique_bytes = self.db.execute(
            "SELECT COALESCE(SUM(size_bytes),0) FROM sources"
        ).fetchone()[0]
        return {
            "root": str(self.root),
            "source_count": int(source_count),
            "reference_count": int(ref_count),
            "derived_count": int(derived_count),
            "text_unit_count": int(text_unit_count),
            "unique_source_bytes": int(unique_bytes),
            "deduplication": "sha256",
            "originals_immutable_by_convention": True,
        }
