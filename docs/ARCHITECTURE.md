# Architecture

## Core Flow

1. The Angular UI uploads resume, job description, and optional reference documents.
2. FastAPI parses documents into text.
3. The RAG pipeline creates parent sections and child chunks.
4. Metadata is attached to each chunk: source type, section, skill tags, document id, and parent id.
5. Retrieval uses query rewriting, vector similarity, keyword scoring, metadata filters, parent expansion, and reranking.
6. The interview service asks questions, records answers, retrieves evidence, scores each answer, and creates a feedback report.
7. Optional web verification extracts answer claims, searches public sources, fetches page text, and returns conservative verdicts with citations.
8. ADK agents can call the same retrieval and scoring tools.

## Local Model Runtime

Ollama is the default local runtime. `app/services/llm.py` calls Ollama's local HTTP API. The ADK files use LiteLLM with the `ollama_chat/...` provider.

## Advanced RAG Components

- `chunking.py`: section-aware, semantic-ish chunking with overlap
- `parent_child.py`: stores large parent sections and retrieves small children
- `hybrid.py`: vector + keyword scoring
- `query_rewriter.py`: multi-query expansion for interview evaluation
- `reranker.py`: cross-encoder hook with a heuristic fallback
- `graph.py`: skill/project/role graph extraction starter
- `evaluation.py`: retrieval and answer quality metrics starter

## Web Verification Components

- `web/search.py`: provider abstraction for DuckDuckGo, Brave Search, Tavily, or disabled mode
- `web/fetcher.py`: safe text extraction from fetched web pages
- `web/verification.py`: claim extraction, source matching, conservative verdicts, and source-backed corrected answers

The local LLM does not browse freely. The backend performs search and source collection, then feedback generation can use the verified evidence.

## Multimodal Components

- Resume parsing supports text files directly and optional PDF/DOCX extraction.
- Audio transcription is designed for `faster-whisper`, with a placeholder fallback.
- Video processing stores files locally and returns coachable communication metrics placeholders.

The first production rule for this project: keep scoring grounded in observable evidence. Do not infer protected traits, personality, emotion, health, or identity from video.
