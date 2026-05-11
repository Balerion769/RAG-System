# RAG Stage Mapping

| Stage | Topic | Project Implementation |
| ----- | ----- | ---------------------- |
| 1 | Basic RAG | Ask questions over resume/JD chunks |
| 2 | Better chunking | Section-aware resume and JD chunking |
| 3 | Multi-document RAG | Resume, JD, company docs, learning notes |
| 4 | Hybrid retrieval | Vector score + keyword score |
| 5 | Conversational + memory | Session history and answer memory |
| 6 | Cross-encoder reranking | Optional sentence-transformers reranker |
| 7 | Metadata filtering + source grounding | Filters by source type, skill, document, section, plus web-grounded claim checks |
| 8 | Advanced chunking strategies | Parent sections, child chunks, overlap, headings |
| 9 | Parent-child retrieval | Retrieve child chunks, cite parent context |
| 10 | Query rewriting & multi-query retrieval | Generate skill, evidence, and role-focused queries |
| 11 | Agentic RAG | ADK agents call retrieval/scoring tools; web verification is exposed through backend tools |
| 12 | Long-term vector memory | Planned user progress store |
| 13 | Graph RAG / Knowledge Graphs | Skill/project/company graph starter |
| 14 | Evaluation pipelines | Retrieval precision, groundedness metric stubs, and web verification scores |
| 15 | Multi-modal RAG | Resume text, transcripts, video/audio metadata |
| 16 | Distributed / scalable RAG systems | Qdrant, queues, async workers planned |
| 17 | Fine-tuned retrieval systems | Future domain training data for embeddings/rerankers |
