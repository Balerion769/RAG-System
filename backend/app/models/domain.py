from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DocumentChunk:
    id: str
    document_id: str
    parent_id: str | None
    text: str
    metadata: dict[str, Any]
    embedding: list[float] = field(default_factory=list)


@dataclass
class SourceDocument:
    id: str
    filename: str
    source_type: str
    text: str
    metadata: dict[str, Any]
    chunks: list[DocumentChunk] = field(default_factory=list)
    parent_chunks: dict[str, DocumentChunk] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float
    vector_score: float = 0.0
    keyword_score: float = 0.0
    rerank_score: float | None = None
    expanded_text: str | None = None


@dataclass
class Evidence:
    chunk_id: str
    document_id: str
    source_type: str
    section: str | None
    score: float
    text: str
    metadata: dict[str, Any]


@dataclass
class InterviewTurn:
    question: str
    answer: str
    feedback: str
    scores: dict[str, float]
    evidence: list[Evidence]
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class InterviewSession:
    id: str
    role_title: str
    resume_document_id: str | None
    job_document_id: str | None
    focus_skills: list[str]
    current_question: str
    turns: list[InterviewTurn] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=utc_now)

