from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from app.models.domain import DocumentChunk


HEADING_PATTERN = re.compile(
    r"^(experience|work experience|projects?|skills?|education|summary|certifications?|"
    r"requirements?|responsibilities|about the role|qualifications?)\b[:\s-]*",
    re.IGNORECASE,
)


@dataclass
class ChunkingConfig:
    child_words: int = 140
    child_overlap: int = 35
    min_child_words: int = 35


class SectionAwareChunker:
    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def build_parent_sections(
        self,
        document_id: str,
        text: str,
        base_metadata: dict,
    ) -> dict[str, DocumentChunk]:
        sections = self._split_sections(text)
        parents: dict[str, DocumentChunk] = {}

        for index, (section_name, section_text) in enumerate(sections):
            parent_id = f"parent-{uuid.uuid4().hex}"
            metadata = {
                **base_metadata,
                "section": section_name,
                "section_index": index,
                "chunk_level": "parent",
            }
            parents[parent_id] = DocumentChunk(
                id=parent_id,
                document_id=document_id,
                parent_id=None,
                text=section_text.strip(),
                metadata=metadata,
            )

        return parents

    def build_child_chunks(
        self,
        document_id: str,
        parents: dict[str, DocumentChunk],
    ) -> list[DocumentChunk]:
        children: list[DocumentChunk] = []
        for parent_id, parent in parents.items():
            words = self._words(parent.text)
            if not words:
                continue

            step = max(1, self.config.child_words - self.config.child_overlap)
            chunk_index = 0
            for start in range(0, len(words), step):
                end = start + self.config.child_words
                chunk_words = words[start:end]
                if len(chunk_words) < self.config.min_child_words and children:
                    break

                text = " ".join(chunk_words)
                metadata = {
                    **parent.metadata,
                    "chunk_level": "child",
                    "chunk_index": chunk_index,
                    "parent_id": parent_id,
                    "skills": extract_skill_tags(text),
                }
                children.append(
                    DocumentChunk(
                        id=f"chunk-{uuid.uuid4().hex}",
                        document_id=document_id,
                        parent_id=parent_id,
                        text=text,
                        metadata=metadata,
                    )
                )
                chunk_index += 1

        return children

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
        sections: list[tuple[str, list[str]]] = []
        current_name = "overview"
        current_lines: list[str] = []

        for line in lines:
            clean = line.strip()
            if clean and HEADING_PATTERN.match(clean) and len(clean.split()) <= 8:
                if current_lines:
                    sections.append((current_name, current_lines))
                current_name = clean.rstrip(":").lower()
                current_lines = []
                continue
            current_lines.append(line)

        if current_lines:
            sections.append((current_name, current_lines))

        if not sections:
            return [("overview", text)]

        return [(name, "\n".join(part).strip()) for name, part in sections if "\n".join(part).strip()]

    def _words(self, text: str) -> list[str]:
        return re.findall(r"\S+", text)


SKILL_KEYWORDS = {
    "python",
    "java",
    "typescript",
    "angular",
    "react",
    "fastapi",
    "django",
    "sql",
    "postgres",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "llm",
    "rag",
    "embeddings",
    "nlp",
    "machine learning",
    "deep learning",
    "vector database",
    "qdrant",
    "weaviate",
    "neo4j",
    "spark",
    "airflow",
    "microservices",
}


def extract_skill_tags(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(skill for skill in SKILL_KEYWORDS if skill in lowered)

