from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    local_model: str


class RagStage(BaseModel):
    stage: int
    topic: str
    status: str
    implementation: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    source_type: str
    chunk_count: int
    parent_count: int
    extracted_characters: int
    metadata: dict[str, Any]


class EvidenceItem(BaseModel):
    chunk_id: str
    document_id: str
    source_type: str
    section: str | None = None
    score: float
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebSourceItem(BaseModel):
    title: str
    url: str
    snippet: str
    provider: str
    fetched_text: str = ""
    score: float = 0.0


class ClaimCheckItem(BaseModel):
    claim: str
    verdict: str
    confidence: float
    explanation: str
    sources: list[WebSourceItem] = Field(default_factory=list)


class VerificationRequest(BaseModel):
    answer: str
    question: str | None = None
    role_title: str | None = None
    max_claims: int = Field(default=5, ge=1, le=8)


class VerificationResponse(BaseModel):
    enabled: bool
    provider: str
    overall_verdict: str
    overall_score: float
    summary: str
    corrected_answer: str
    claims: list[ClaimCheckItem] = Field(default_factory=list)
    sources: list[WebSourceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class StartInterviewRequest(BaseModel):
    role_title: str = "AI/ML Engineer"
    resume_document_id: str | None = None
    job_document_id: str | None = None
    focus_skills: list[str] = Field(default_factory=list)


class StartInterviewResponse(BaseModel):
    session_id: str
    question: str
    evidence: list[EvidenceItem]


class AnswerRequest(BaseModel):
    answer: str
    web_verification: bool = False


class AnswerResponse(BaseModel):
    session_id: str
    feedback: str
    scores: dict[str, float]
    next_question: str
    evidence: list[EvidenceItem]
    verification: VerificationResponse | None = None


class VideoUploadResponse(BaseModel):
    session_id: str
    filename: str
    saved_path: str
    metrics: dict[str, Any]


class InterviewTurnResponse(BaseModel):
    question: str
    answer: str
    feedback: str
    scores: dict[str, float]
    evidence: list[EvidenceItem]
    verification: VerificationResponse | None = None
    created_at: datetime


class ReportResponse(BaseModel):
    session_id: str
    role_title: str
    status: str
    turns: list[InterviewTurnResponse]
    overall_scores: dict[str, float]
    improvement_plan: list[str]
    created_at: datetime
