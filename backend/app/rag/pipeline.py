from __future__ import annotations

import uuid

from app.models.domain import Evidence, SourceDocument
from app.rag.chunking import SectionAwareChunker, extract_skill_tags
from app.rag.embeddings import get_embedding_model
from app.rag.graph import LocalKnowledgeGraphBuilder
from app.rag.hybrid import HybridRetriever, KeywordIndex
from app.rag.parent_child import ParentChildExpander
from app.rag.query_rewriter import OfflineQueryRewriter
from app.rag.reranker import get_reranker
from app.rag.vector_store import InMemoryVectorStore
from app.storage.repositories import repository


class AdvancedRagPipeline:
    def __init__(self) -> None:
        self.embedding_model = get_embedding_model()
        self.vector_store = InMemoryVectorStore()
        self.keyword_index = KeywordIndex()
        self.chunker = SectionAwareChunker()
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            keyword_index=self.keyword_index,
            embedding_model=self.embedding_model,
        )
        self.reranker = get_reranker()
        self.query_rewriter = OfflineQueryRewriter()
        self.parent_child = ParentChildExpander()
        self.graph_builder = LocalKnowledgeGraphBuilder()

    def ingest_document(
        self,
        filename: str,
        source_type: str,
        text: str,
        metadata: dict | None = None,
    ) -> SourceDocument:
        document_id = f"doc-{uuid.uuid4().hex}"
        base_metadata = {
            "document_id": document_id,
            "filename": filename,
            "source_type": source_type,
            **(metadata or {}),
        }

        parents = self.chunker.build_parent_sections(document_id, text, base_metadata)
        children = self.chunker.build_child_chunks(document_id, parents)
        embeddings = self.embedding_model.embed([child.text for child in children]) if children else []
        for child, embedding in zip(children, embeddings):
            child.embedding = embedding

        graph = self.graph_builder.build(document_id, text)
        source_document = SourceDocument(
            id=document_id,
            filename=filename,
            source_type=source_type,
            text=text,
            metadata={
                **base_metadata,
                "skills": extract_skill_tags(text),
                "graph_nodes": len(graph.nodes),
                "graph_edges": len(graph.edges),
            },
            chunks=children,
            parent_chunks=parents,
        )
        repository.save_document(source_document)
        self.vector_store.upsert(children)
        self.keyword_index.upsert(children)
        return source_document

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        filters: dict | None = None,
        role_title: str | None = None,
        skills: list[str] | None = None,
    ) -> list[Evidence]:
        rewrites = self.query_rewriter.rewrite(query, role_title=role_title, skills=skills)
        merged = {}
        for rewritten_query in rewrites:
            for result in self.retriever.retrieve(rewritten_query, top_k=top_k, filters=filters):
                current = merged.get(result.chunk.id)
                if not current or result.score > current.score:
                    merged[result.chunk.id] = result

        ranked = self.reranker.rerank(query, list(merged.values()), top_k=top_k)

        parent_lookup = {}
        for document in repository.list_documents():
            parent_lookup.update(document.parent_chunks)

        expanded = self.parent_child.expand(ranked, parent_lookup)
        return [
            Evidence(
                chunk_id=item.chunk.id,
                document_id=item.chunk.document_id,
                source_type=item.chunk.metadata.get("source_type", "unknown"),
                section=item.chunk.metadata.get("section"),
                score=round(float(item.score), 4),
                text=(item.expanded_text or item.chunk.text).strip(),
                metadata=item.chunk.metadata,
            )
            for item in expanded
        ]

