from __future__ import annotations

from app.core.config import settings
from app.agents.tools import retrieve_interview_evidence, score_interview_answer


root_agent = None

try:
    try:
        from google.adk.agents import Agent
    except ImportError:
        from google.adk.agents.llm_agent import Agent
    from google.adk.models.lite_llm import LiteLlm

    root_agent = Agent(
        model=LiteLlm(model=f"ollama_chat/{settings.ollama_model}"),
        name="ai_interview_coach",
        description="Conducts source-grounded mock interviews using local RAG evidence.",
        instruction=(
            "You are an AI interview coach. Ask rigorous interview questions, retrieve evidence "
            "before scoring, and give practical feedback grounded only in uploaded resume, job "
            "description, transcript, or reference evidence. Never infer protected traits or hidden "
            "personality attributes from video/audio."
        ),
        tools=[retrieve_interview_evidence, score_interview_answer],
    )
except Exception:
    root_agent = None

