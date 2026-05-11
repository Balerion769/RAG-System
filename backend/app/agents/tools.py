from __future__ import annotations

from app.rag.pipeline import AdvancedRagPipeline
from app.services.interview_service import build_feedback


_pipeline = AdvancedRagPipeline()


def retrieve_interview_evidence(query: str) -> dict:
    """Retrieve grounded resume/JD evidence for an interview question or answer."""

    evidence = _pipeline.retrieve(query=query, top_k=5)
    return {
        "items": [
            {
                "source_type": item.source_type,
                "section": item.section,
                "score": item.score,
                "text": item.text[:900],
            }
            for item in evidence
        ]
    }


def score_interview_answer(question: str, answer: str) -> dict:
    """Return a simple rubric score for an interview answer."""

    evidence = _pipeline.retrieve(f"{question}\n{answer}", top_k=5)
    word_count = len(answer.split())
    grounding = min(1.0, len(evidence) / 5)
    scores = {
        "technical_depth": min(100, 35 + word_count * 0.4 + grounding * 25),
        "source_grounding": min(100, 30 + grounding * 70),
        "communication": min(100, 45 + word_count * 0.3),
        "role_relevance": min(100, 40 + grounding * 45),
    }
    return {"scores": scores, "feedback": build_feedback(scores, evidence)}

