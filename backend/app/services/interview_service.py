from __future__ import annotations

import statistics
import uuid

from app.models.domain import Evidence, InterviewSession, InterviewTurn
from app.rag.evaluation import RagEvaluator
from app.rag.pipeline import AdvancedRagPipeline
from app.schemas import StartInterviewRequest
from app.services.llm import LocalLLMClient
from app.storage.repositories import repository


class InterviewService:
    def __init__(self, pipeline: AdvancedRagPipeline) -> None:
        self.pipeline = pipeline
        self.llm = LocalLLMClient()
        self.evaluator = RagEvaluator()

    async def start_interview(self, request: StartInterviewRequest) -> tuple[InterviewSession, list[Evidence]]:
        evidence = self.pipeline.retrieve(
            query=f"{request.role_title} important interview skills projects responsibilities",
            top_k=5,
            filters=self._document_filter(request.resume_document_id, request.job_document_id),
            role_title=request.role_title,
            skills=request.focus_skills,
        )
        fallback_question = (
            f"Tell me about a project from your resume that best proves you are ready for a "
            f"{request.role_title} role. Include your role, technical choices, and measurable impact."
        )
        question = await self.llm.generate(
            system="You are a rigorous but supportive technical interviewer.",
            prompt=(
                "Create one first interview question. Ground it in this evidence when possible:\n\n"
                f"{format_evidence(evidence)}\n\nRole: {request.role_title}"
            ),
            fallback=fallback_question,
        )
        session = InterviewSession(
            id=f"session-{uuid.uuid4().hex}",
            role_title=request.role_title,
            resume_document_id=request.resume_document_id,
            job_document_id=request.job_document_id,
            focus_skills=request.focus_skills,
            current_question=question.strip(),
        )
        repository.save_session(session)
        return session, evidence

    async def submit_answer(self, session_id: str, answer: str) -> tuple[InterviewSession, InterviewTurn]:
        session = repository.get_session(session_id)
        if not session:
            raise KeyError(f"Interview session not found: {session_id}")

        query = f"{session.current_question}\nCandidate answer:\n{answer}"
        evidence = self.pipeline.retrieve(
            query=query,
            top_k=6,
            filters=self._document_filter(session.resume_document_id, session.job_document_id),
            role_title=session.role_title,
            skills=session.focus_skills,
        )
        scores = self._score_answer(session.current_question, answer, evidence)
        fallback_feedback = build_feedback(scores, evidence)
        feedback = await self.llm.generate(
            system=(
                "You are an interview coach. Give direct, kind feedback grounded only in the "
                "resume/JD evidence and the candidate answer. Do not infer protected traits."
            ),
            prompt=(
                f"Question:\n{session.current_question}\n\nAnswer:\n{answer}\n\n"
                f"Scores:\n{scores}\n\nEvidence:\n{format_evidence(evidence)}\n\n"
                "Return concise feedback with strengths, gaps, and one improvement action."
            ),
            fallback=fallback_feedback,
        )
        next_question = await self.llm.generate(
            system="You are a technical interviewer creating adaptive follow-up questions.",
            prompt=(
                f"Role: {session.role_title}\nPrevious question: {session.current_question}\n"
                f"Candidate answer: {answer}\nScores: {scores}\n"
                "Ask one targeted follow-up question that tests depth or improves a weak area."
            ),
            fallback=make_follow_up(session.role_title, scores),
        )

        turn = InterviewTurn(
            question=session.current_question,
            answer=answer,
            feedback=feedback.strip(),
            scores=scores,
            evidence=evidence,
        )
        session.turns.append(turn)
        session.current_question = next_question.strip()
        repository.save_session(session)
        return session, turn

    def build_report(self, session_id: str) -> InterviewSession:
        session = repository.get_session(session_id)
        if not session:
            raise KeyError(f"Interview session not found: {session_id}")
        return session

    def overall_scores(self, session: InterviewSession) -> dict[str, float]:
        if not session.turns:
            return {}
        keys = sorted({key for turn in session.turns for key in turn.scores})
        return {
            key: round(statistics.mean(turn.scores[key] for turn in session.turns if key in turn.scores), 1)
            for key in keys
        }

    def improvement_plan(self, session: InterviewSession) -> list[str]:
        scores = self.overall_scores(session)
        if not scores:
            return ["Complete at least one interview answer to generate a personalized plan."]
        lowest = sorted(scores.items(), key=lambda item: item[1])[:3]
        actions = {
            "technical_depth": "Add implementation details: architecture, tradeoffs, complexity, and failure handling.",
            "source_grounding": "Connect claims to specific resume projects, metrics, or job requirements.",
            "communication": "Use a tighter STAR structure: situation, task, action, result.",
            "role_relevance": "Map each answer back to the target role's responsibilities and required skills.",
        }
        return [actions.get(key, f"Practice improving {key.replace('_', ' ')}.") for key, _ in lowest]

    def _score_answer(self, question: str, answer: str, evidence: list[Evidence]) -> dict[str, float]:
        word_count = len(answer.split())
        groundedness = self.evaluator.groundedness_proxy(answer, evidence)
        relevance = self.evaluator.retrieval_coverage(question, evidence)
        structure_bonus = 1 if any(word in answer.lower() for word in ["because", "result", "impact"]) else 0

        technical_depth = clamp(35 + min(35, word_count * 0.45) + groundedness * 30)
        source_grounding = clamp(30 + groundedness * 70)
        communication = clamp(40 + min(35, word_count * 0.35) + structure_bonus * 15)
        role_relevance = clamp(35 + relevance * 45 + min(20, len(evidence) * 3))

        return {
            "technical_depth": round(technical_depth, 1),
            "source_grounding": round(source_grounding, 1),
            "communication": round(communication, 1),
            "role_relevance": round(role_relevance, 1),
        }

    def _document_filter(self, resume_document_id: str | None, job_document_id: str | None) -> dict | None:
        document_ids = [item for item in [resume_document_id, job_document_id] if item]
        if not document_ids:
            return None
        return {"document_id": document_ids}


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "No evidence retrieved yet."
    lines = []
    for index, item in enumerate(evidence, start=1):
        text = " ".join(item.text.split())[:700]
        lines.append(f"{index}. [{item.source_type}/{item.section}] {text}")
    return "\n".join(lines)


def build_feedback(scores: dict[str, float], evidence: list[Evidence]) -> str:
    strongest = max(scores.items(), key=lambda item: item[1])[0]
    weakest = min(scores.items(), key=lambda item: item[1])[0]
    source_note = "I found supporting resume/JD evidence." if evidence else "I could not find strong source evidence yet."
    return (
        f"Strongest area: {strongest.replace('_', ' ')}. "
        f"Main improvement area: {weakest.replace('_', ' ')}. {source_note} "
        "Improve the answer by adding a concrete project example, your exact contribution, "
        "technical tradeoffs, and measurable result."
    )


def make_follow_up(role_title: str, scores: dict[str, float]) -> str:
    weakest = min(scores.items(), key=lambda item: item[1])[0]
    if weakest == "technical_depth":
        return f"Go deeper technically: what architecture or implementation tradeoff mattered most for this {role_title} work?"
    if weakest == "source_grounding":
        return "Which exact resume project or metric proves this claim, and what evidence should I use to trust it?"
    if weakest == "communication":
        return "Can you restate the same answer using situation, task, action, and result in under two minutes?"
    return f"How does that experience map directly to the responsibilities of a {role_title}?"

