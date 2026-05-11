from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.multimodal.resume import extract_text_from_upload
from app.multimodal.video import save_video_upload
from app.rag.pipeline import AdvancedRagPipeline
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    DocumentUploadResponse,
    EvidenceItem,
    HealthResponse,
    RagStage,
    ReportResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    VerificationRequest,
    VerificationResponse,
    VideoUploadResponse,
)
from app.services.interview_service import InterviewService


router = APIRouter()
pipeline = AdvancedRagPipeline()
interview_service = InterviewService(pipeline)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, local_model=settings.ollama_model)


@router.get("/rag/stages", response_model=list[RagStage])
async def rag_stages() -> list[RagStage]:
    return [
        RagStage(stage=1, topic="Basic RAG", status="implemented", implementation="resume/JD QA"),
        RagStage(stage=2, topic="Better chunking", status="implemented", implementation="section-aware chunks"),
        RagStage(stage=3, topic="Multi-document RAG", status="implemented", implementation="source_type metadata"),
        RagStage(stage=4, topic="Hybrid retrieval", status="implemented", implementation="vector + BM25-like scoring"),
        RagStage(stage=5, topic="Conversational + memory", status="implemented", implementation="session turns"),
        RagStage(stage=6, topic="Cross-encoder reranking", status="ready", implementation="optional model fallback"),
        RagStage(stage=7, topic="Metadata filtering", status="implemented", implementation="document/source filters"),
        RagStage(stage=8, topic="Advanced chunking", status="implemented", implementation="parent and child chunks"),
        RagStage(stage=9, topic="Parent-child retrieval", status="implemented", implementation="child hit, parent context"),
        RagStage(stage=10, topic="Query rewriting", status="implemented", implementation="offline multi-query"),
        RagStage(stage=11, topic="Agentic RAG", status="ready", implementation="ADK tools and agent files"),
        RagStage(stage=12, topic="Long-term vector memory", status="planned", implementation="progress memory store"),
        RagStage(stage=13, topic="Graph RAG", status="starter", implementation="local skill/project graph"),
        RagStage(stage=14, topic="Evaluation pipelines", status="starter", implementation="groundedness metrics"),
        RagStage(stage=15, topic="Multimodal RAG", status="starter", implementation="resume/video/audio hooks"),
        RagStage(stage=16, topic="Distributed RAG", status="planned", implementation="Qdrant + workers"),
        RagStage(stage=17, topic="Fine-tuned retrieval", status="planned", implementation="future training data"),
    ]


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form("resume"),
) -> DocumentUploadResponse:
    content = await file.read()
    filename = file.filename or "upload.txt"
    text = extract_text_from_upload(filename, content).strip()
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file.")

    document = pipeline.ingest_document(
        filename=filename,
        source_type=source_type,
        text=text,
        metadata={"original_content_type": file.content_type},
    )
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        source_type=document.source_type,
        chunk_count=len(document.chunks),
        parent_count=len(document.parent_chunks),
        extracted_characters=len(document.text),
        metadata=document.metadata,
    )


@router.post("/interviews/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    session, evidence = await interview_service.start_interview(request)
    return StartInterviewResponse(
        session_id=session.id,
        question=session.current_question,
        evidence=[to_evidence_item(item) for item in evidence],
    )


@router.post("/interviews/{session_id}/answer", response_model=AnswerResponse)
async def answer_question(session_id: str, request: AnswerRequest) -> AnswerResponse:
    try:
        session, turn = await interview_service.submit_answer(
            session_id,
            request.answer,
            web_verification=request.web_verification,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AnswerResponse(
        session_id=session.id,
        feedback=turn.feedback,
        scores=turn.scores,
        next_question=session.current_question,
        evidence=[to_evidence_item(item) for item in turn.evidence],
        verification=to_verification_response(turn.verification),
    )


@router.post("/verification/check", response_model=VerificationResponse)
async def check_answer_verification(request: VerificationRequest) -> VerificationResponse:
    report = await interview_service.verification_service.verify_answer(
        answer=request.answer,
        question=request.question,
        role_title=request.role_title,
        max_claims=request.max_claims,
    )
    return VerificationResponse(**asdict(report))


@router.post("/interviews/{session_id}/video", response_model=VideoUploadResponse)
async def upload_interview_video(
    session_id: str,
    file: UploadFile = File(...),
) -> VideoUploadResponse:
    content = await file.read()
    filename = file.filename or "interview.webm"
    saved_path, metrics = save_video_upload(session_id, filename, content)
    return VideoUploadResponse(
        session_id=session_id,
        filename=filename,
        saved_path=str(saved_path),
        metrics=metrics,
    )


@router.get("/interviews/{session_id}/report", response_model=ReportResponse)
async def interview_report(session_id: str) -> ReportResponse:
    try:
        session = interview_service.build_report(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ReportResponse(
        session_id=session.id,
        role_title=session.role_title,
        status=session.status,
        turns=[
            {
                "question": turn.question,
                "answer": turn.answer,
                "feedback": turn.feedback,
                "scores": turn.scores,
                "evidence": [to_evidence_item(item) for item in turn.evidence],
                "verification": to_verification_response(turn.verification),
                "created_at": turn.created_at,
            }
            for turn in session.turns
        ],
        overall_scores=interview_service.overall_scores(session),
        improvement_plan=interview_service.improvement_plan(session),
        created_at=session.created_at,
    )


def to_evidence_item(item) -> EvidenceItem:
    data = asdict(item)
    return EvidenceItem(**data)


def to_verification_response(data: dict | None) -> VerificationResponse | None:
    if not data:
        return None
    return VerificationResponse(**data)
