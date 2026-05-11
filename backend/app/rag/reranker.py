from __future__ import annotations

from app.core.config import settings
from app.models.domain import RetrievedChunk
from app.rag.hybrid import tokenize


class HeuristicCrossEncoderReranker:
    def rerank(self, query: str, results: list[RetrievedChunk], top_k: int = 6) -> list[RetrievedChunk]:
        query_terms = set(tokenize(query))
        for result in results:
            terms = set(tokenize(result.chunk.text))
            overlap = len(query_terms & terms) / max(1, len(query_terms))
            result.rerank_score = 0.7 * result.score + 0.3 * overlap
            result.score = result.rerank_score
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


class SentenceTransformerCrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, results: list[RetrievedChunk], top_k: int = 6) -> list[RetrievedChunk]:
        if not results:
            return []
        pairs = [(query, result.chunk.text) for result in results]
        scores = self.model.predict(pairs)
        for result, score in zip(results, scores):
            result.rerank_score = float(score)
            result.score = float(score)
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def get_reranker() -> HeuristicCrossEncoderReranker | SentenceTransformerCrossEncoderReranker:
    if settings.reranker_provider.lower() not in {"cross_encoder", "cross-encoder"}:
        return HeuristicCrossEncoderReranker()
    try:
        return SentenceTransformerCrossEncoderReranker(settings.cross_encoder_model)
    except Exception:
        return HeuristicCrossEncoderReranker()
