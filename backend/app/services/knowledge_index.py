from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from app.services.models import Chapter


@dataclass
class SearchHit:
    title: str
    score: float
    timestamp: float
    snippet: str


class KnowledgeIndex:
    """Lightweight hash-based embedding index (placeholder for production embeddings)."""

    def __init__(self, dimension: int = 128) -> None:
        self._dimension = dimension
        self._vectors: list[np.ndarray] = []
        self._chapters: list[Chapter] = []

    def build(self, chapters: list[Chapter]) -> None:
        self._chapters = chapters
        self._vectors = [self._embed(chapter.content) for chapter in chapters]

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        if not self._vectors:
            return []
        query_vec = self._embed(query)
        scores = [self._cosine(query_vec, vector) for vector in self._vectors]
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        results: list[SearchHit] = []
        for index, score in ranked:
            chapter = self._chapters[index]
            snippet = chapter.content[:180] + ("..." if len(chapter.content) > 180 else "")
            results.append(SearchHit(title=chapter.title, score=score, timestamp=chapter.timestamp, snippet=snippet))
        return results

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dimension, dtype=np.float32)
        tokens = re.findall(r"[A-Za-z]{3,}", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            bucket = hash(token) % self._dimension
            vector[bucket] += 1.0
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    @staticmethod
    def _cosine(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        if not denom:
            return 0.0
        return float(np.dot(vec_a, vec_b) / denom)
