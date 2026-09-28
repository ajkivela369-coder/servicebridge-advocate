from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from servicebridge.models import EvidenceChunk, EvidenceClass, RetrievalHit
from servicebridge.store import EvidenceStore

from .memory import LocalVectorStore


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class LocalSemanticEvidenceStore:
    """
    Hybrid local retriever: SQLite FTS + local embeddings.

    It implements the same .search() contract Advocate already expects.
    """

    base: EvidenceStore
    vectors: LocalVectorStore
    embedder: EmbeddingProvider

    def index(self, *, batch_size: int = 32) -> int:
        records = self.base.list_index_records()
        count = 0
        for start in range(0, len(records), max(1, int(batch_size))):
            batch = records[start : start + batch_size]
            texts = [str(x["text"]) for x in batch]
            embeddings = self.embedder.embed(texts)
            if len(embeddings) != len(batch):
                raise RuntimeError("Embedding count does not match evidence chunk count.")
            for record, vector in zip(batch, embeddings):
                self.vectors.upsert(
                    str(record["chunk_id"]),
                    str(record["text"]),
                    vector,
                    {
                        "source_id": record["source_id"],
                        "ordinal": record["ordinal"],
                        "locator": record["locator"],
                        "evidence_class": record["evidence_class"],
                        "title": record["title"],
                    },
                )
                count += 1
        return count

    def search(self, query: str, limit: int = 8) -> list[RetrievalHit]:
        lexical = self.base.search(query, limit=max(limit * 2, limit))
        query_vectors = self.embedder.embed([query])
        semantic_raw = (
            self.vectors.search(query_vectors[0], limit=max(limit * 2, limit))
            if query_vectors
            else []
        )

        semantic: list[RetrievalHit] = []
        for item in semantic_raw:
            meta = item.metadata
            try:
                evidence_class = EvidenceClass(str(meta["evidence_class"]))
            except Exception:
                continue
            semantic.append(
                RetrievalHit(
                    chunk=EvidenceChunk(
                        chunk_id=item.item_id,
                        source_id=str(meta.get("source_id", "")),
                        text=item.text,
                        ordinal=int(meta.get("ordinal", 0)),
                        locator=meta.get("locator"),
                        evidence_class=evidence_class,
                    ),
                    title=str(meta.get("title", "")),
                    score=float(item.score),
                )
            )

        return reciprocal_rank_fusion(lexical, semantic, limit=limit)

    def list_sources(self):
        return self.base.list_sources()


def reciprocal_rank_fusion(
    lexical: list[RetrievalHit],
    semantic: list[RetrievalHit],
    *,
    limit: int = 8,
    k: int = 60,
) -> list[RetrievalHit]:
    by_id: dict[str, RetrievalHit] = {}
    scores: dict[str, float] = {}

    for ranked in (lexical, semantic):
        for rank, hit in enumerate(ranked, start=1):
            chunk_id = hit.chunk.chunk_id
            by_id[chunk_id] = hit
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    ordered = sorted(scores, key=scores.get, reverse=True)
    out = []
    for chunk_id in ordered[: max(0, int(limit))]:
        hit = by_id[chunk_id]
        out.append(
            RetrievalHit(
                chunk=hit.chunk,
                title=hit.title,
                score=scores[chunk_id],
            )
        )
    return out
