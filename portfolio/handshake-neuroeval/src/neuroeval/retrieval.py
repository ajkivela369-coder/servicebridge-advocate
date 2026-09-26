from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class RetrievalItem:
    item_id: str
    text: str


@dataclass(frozen=True)
class RetrievalHit:
    item_id: str
    text: str
    score: float


class TfidfRetrievalIndex:
    """Classical NLP retrieval baseline.

    This is intentionally not called an embedding model. TF-IDF is a lexical
    vectorization baseline that gives us something measurable to compare with
    future embedding-based semantic retrieval.
    """

    def __init__(self, items: Iterable[RetrievalItem]):
        self.items = list(items)
        if not self.items:
            raise ValueError("at least one retrieval item is required")
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform([item.text for item in self.items])

    def search(self, query: str, limit: int = 5) -> list[RetrievalHit]:
        if not query.strip():
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        ranked = sorted(
            enumerate(scores),
            key=lambda pair: pair[1],
            reverse=True,
        )[: max(0, limit)]
        return [
            RetrievalHit(
                item_id=self.items[index].item_id,
                text=self.items[index].text,
                score=float(score),
            )
            for index, score in ranked
            if score > 0
        ]
