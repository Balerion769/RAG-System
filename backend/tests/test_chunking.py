from app.rag.chunking import SectionAwareChunker, extract_skill_tags


def test_section_aware_chunker_creates_parent_and_child_chunks() -> None:
    text = """
Summary
Python engineer building RAG systems.

Projects
Built an Angular and FastAPI interview coach with embeddings and Qdrant.
The system used hybrid retrieval, reranking, and grounded feedback.
"""
    chunker = SectionAwareChunker()
    parents = chunker.build_parent_sections("doc-1", text, {"source_type": "resume"})
    children = chunker.build_child_chunks("doc-1", parents)

    assert parents
    assert children
    assert all(child.parent_id in parents for child in children)


def test_skill_tags_detect_known_terms() -> None:
    tags = extract_skill_tags("Python FastAPI Angular embeddings Qdrant")
    assert "python" in tags
    assert "fastapi" in tags
    assert "angular" in tags
    assert "qdrant" in tags

