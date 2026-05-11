from __future__ import annotations

from app.models.domain import DocumentChunk, RetrievedChunk
from app.rag.embeddings import cosine_similarity


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: dict[str, DocumentChunk] = {}

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.id] = chunk

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 8,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        filters = filters or {}
        results: list[RetrievedChunk] = []

        for chunk in self._chunks.values():
            if not metadata_matches(chunk.metadata, filters):
                continue
            score = cosine_similarity(query_embedding, chunk.embedding)
            results.append(RetrievedChunk(chunk=chunk, score=score, vector_score=score))

        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def metadata_matches(metadata: dict, filters: dict) -> bool:
    for key, expected in filters.items():
        if expected is None:
            continue
        actual = metadata.get(key)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True

