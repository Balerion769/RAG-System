from __future__ import annotations

from app.models.domain import Evidence
from app.rag.hybrid import tokenize


class RagEvaluator:
    def retrieval_coverage(self, query: str, evidence: list[Evidence]) -> float:
        query_terms = set(tokenize(query))
        if not query_terms or not evidence:
            return 0.0
        evidence_terms = set()
        for item in evidence:
            evidence_terms.update(tokenize(item.text))
        return len(query_terms & evidence_terms) / len(query_terms)

    def groundedness_proxy(self, answer: str, evidence: list[Evidence]) -> float:
        answer_terms = set(tokenize(answer))
        if not answer_terms or not evidence:
            return 0.0
        evidence_terms = set()
        for item in evidence:
            evidence_terms.update(tokenize(item.text))
        return len(answer_terms & evidence_terms) / len(answer_terms)

