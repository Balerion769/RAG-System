from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from app.models.domain import DocumentChunk, RetrievedChunk
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import InMemoryVectorStore, metadata_matches


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.\-]+")


class KeywordIndex:
    def __init__(self) -> None:
        self._chunks: dict[str, DocumentChunk] = {}
        self._term_counts: dict[str, Counter[str]] = {}
        self._doc_freq: Counter[str] = Counter()
        self._lengths: dict[str, int] = {}

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            counts = Counter(tokens)
            self._chunks[chunk.id] = chunk
            self._term_counts[chunk.id] = counts
            self._lengths[chunk.id] = max(1, sum(counts.values()))
            for term in counts:
                self._doc_freq[term] += 1

    def search(self, query: str, top_k: int = 8, filters: dict | None = None) -> list[RetrievedChunk]:
        filters = filters or {}
        query_terms = tokenize(query)
        if not query_terms:
            return []

        avg_len = sum(self._lengths.values()) / max(1, len(self._lengths))
        total_docs = max(1, len(self._chunks))
        scores: defaultdict[str, float] = defaultdict(float)
        k1 = 1.5
        b = 0.75

        for chunk_id, counts in self._term_counts.items():
            chunk = self._chunks[chunk_id]
            if not metadata_matches(chunk.metadata, filters):
                continue
            doc_len = self._lengths[chunk_id]
            for term in query_terms:
                if term not in counts:
                    continue
                df = self._doc_freq[term]
                idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
                tf = counts[term]
                denom = tf + k1 * (1 - b + b * doc_len / avg_len)
                scores[chunk_id] += idf * (tf * (k1 + 1)) / denom

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            RetrievedChunk(
                chunk=self._chunks[chunk_id],
                score=score,
                keyword_score=score,
            )
            for chunk_id, score in ranked
        ]


class HybridRetriever:
    def __init__(
        self,
        vector_store: InMemoryVectorStore,
        keyword_index: KeywordIndex,
        embedding_model: EmbeddingModel,
        vector_weight: float = 0.65,
        keyword_weight: float = 0.35,
    ) -> None:
        self.vector_store = vector_store
        self.keyword_index = keyword_index
        self.embedding_model = embedding_model
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def retrieve(self, query: str, top_k: int = 8, filters: dict | None = None) -> list[RetrievedChunk]:
        query_embedding = self.embedding_model.embed([query])[0]
        vector_results = self.vector_store.query(query_embedding, top_k=top_k, filters=filters)
        keyword_results = self.keyword_index.search(query, top_k=top_k, filters=filters)

        merged: dict[str, RetrievedChunk] = {}
        max_keyword = max((item.keyword_score for item in keyword_results), default=1.0) or 1.0

        for item in vector_results:
            merged[item.chunk.id] = item

        for item in keyword_results:
            normalized_keyword = item.keyword_score / max_keyword
            existing = merged.get(item.chunk.id)
            if existing:
                existing.keyword_score = normalized_keyword
            else:
                item.keyword_score = normalized_keyword
                merged[item.chunk.id] = item

        for item in merged.values():
            item.score = self.vector_weight * item.vector_score + self.keyword_weight * item.keyword_score

        return sorted(merged.values(), key=lambda result: result.score, reverse=True)[:top_k]


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())

