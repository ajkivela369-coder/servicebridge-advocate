from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import sqlite3
from typing import Any
from urllib.request import Request, urlopen

from .runtime import RuntimePolicy


@dataclass(frozen=True)
class VectorHit:
    item_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class LocalEmbeddingClient:
    """OpenAI-compatible local embedding client, intended for llama.cpp localhost."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1/embeddings",
        model: str = "local-embedding-model",
        policy: RuntimePolicy | None = None,
        timeout: float = 120.0,
    ):
        self.endpoint = endpoint
        self.model = model
        self.policy = policy or RuntimePolicy()
        self.timeout = timeout
        self.policy.assert_url_allowed(endpoint)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self.policy.assert_url_allowed(self.endpoint)
        payload = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float",
        }
        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
        vectors = [row.get("embedding") for row in rows]
        if len(vectors) != len(texts) or any(not isinstance(v, list) for v in vectors):
            raise RuntimeError("Local embedding server returned an unexpected response.")
        return [[float(x) for x in vector] for vector in vectors]


class LocalVectorStore:
    """
    Dependency-free SQLite vector store.

    This intentionally uses Python cosine scoring instead of requiring a hosted
    vector database. sqlite-vec can replace the scorer later without changing
    the app-facing contract.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS vectors (
                item_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "LocalVectorStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert(
        self,
        item_id: str,
        text: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not vector:
            raise ValueError("Vector must not be empty.")
        with self.db:
            self.db.execute(
                """
                INSERT INTO vectors (item_id, text, vector_json, metadata_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    text=excluded.text,
                    vector_json=excluded.vector_json,
                    metadata_json=excluded.metadata_json
                """,
                (
                    item_id,
                    text,
                    json.dumps([float(x) for x in vector]),
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )

    def search(self, query_vector: list[float], limit: int = 8) -> list[VectorHit]:
        if not query_vector:
            return []
        rows = self.db.execute("SELECT * FROM vectors").fetchall()
        scored: list[VectorHit] = []
        for row in rows:
            vector = [float(x) for x in json.loads(row["vector_json"])]
            if len(vector) != len(query_vector):
                continue
            score = cosine_similarity(query_vector, vector)
            scored.append(
                VectorHit(
                    item_id=row["item_id"],
                    text=row["text"],
                    score=score,
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: max(0, int(limit))]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Vectors must be non-empty and have equal dimensions.")
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    na = math.sqrt(sum(float(x) ** 2 for x in a))
    nb = math.sqrt(sum(float(y) ** 2 for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
