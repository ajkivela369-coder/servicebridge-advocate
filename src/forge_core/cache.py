from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import time
from typing import Any

from servicebridge.local_runtime.runtime import AssetCache


def stable_cache_key(namespace: str, payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    digest = sha256(raw).hexdigest()
    return f"{namespace}:{digest}"


class ForgeProjectCache:
    """Content-addressed cache index shared across Forge-backed apps."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.assets = AssetCache(self.root / "assets")
        self.db = sqlite3.connect(self.root / "project-cache.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                namespace TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_hit REAL NOT NULL,
                hit_count INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cache_namespace
            ON cache_entries(namespace, last_hit DESC);
            """
        )

    def close(self) -> None:
        self.assets.close()
        self.db.close()

    def __enter__(self) -> "ForgeProjectCache":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get(self, namespace: str, payload: Any) -> dict[str, Any] | None:
        key = stable_cache_key(namespace, payload)
        row = self.db.execute(
            "SELECT * FROM cache_entries WHERE cache_key=?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        asset = self.assets.get(row["asset_id"])
        if not asset or not Path(asset["path"]).is_file():
            with self.db:
                self.db.execute(
                    "DELETE FROM cache_entries WHERE cache_key=?",
                    (key,),
                )
            return None
        with self.db:
            self.db.execute(
                """
                UPDATE cache_entries
                SET last_hit=?, hit_count=hit_count+1
                WHERE cache_key=?
                """,
                (time.time(), key),
            )
        return {
            "cache_key": key,
            "asset": asset,
            "metadata": json.loads(row["metadata_json"]),
            "hit": True,
            "hit_count": int(row["hit_count"]) + 1,
        }

    def put_bytes(
        self,
        namespace: str,
        payload: Any,
        data: bytes,
        *,
        kind: str,
        suffix: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        key = stable_cache_key(namespace, payload)
        asset = self.assets.put(
            data,
            kind=kind,
            suffix=suffix,
            provenance={
                "forge_cache_key": key,
                **(metadata or {}),
            },
        )
        now = time.time()
        with self.db:
            self.db.execute(
                """
                INSERT INTO cache_entries
                (cache_key, namespace, asset_id, metadata_json, created_at,
                 last_hit, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(cache_key) DO UPDATE SET
                    asset_id=excluded.asset_id,
                    metadata_json=excluded.metadata_json,
                    last_hit=excluded.last_hit
                """,
                (
                    key,
                    namespace,
                    asset["asset_id"],
                    json.dumps(metadata or {}, sort_keys=True),
                    now,
                    now,
                ),
            )
        return {
            "cache_key": key,
            "asset": asset,
            "metadata": metadata or {},
            "hit": False,
            "hit_count": 0,
        }

    def status(self) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT COUNT(*) AS entries, COALESCE(SUM(hit_count),0) AS hits FROM cache_entries"
        ).fetchone()
        return {
            "entries": int(row["entries"]),
            "hits": int(row["hits"]),
            "root": str(self.root),
        }
