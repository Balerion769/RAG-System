from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.rag.chunking import SKILL_KEYWORDS, extract_skill_tags


@dataclass
class KnowledgeNode:
    id: str
    label: str
    type: str
    properties: dict = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source: str
    target: str
    type: str
    properties: dict = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]


class LocalKnowledgeGraphBuilder:
    def build(self, document_id: str, text: str) -> KnowledgeGraph:
        skills = extract_skill_tags(text)
        project_names = extract_project_names(text)

        nodes = [KnowledgeNode(id=document_id, label=document_id, type="document")]
        edges: list[KnowledgeEdge] = []

        for skill in skills:
            skill_id = f"skill:{skill}"
            nodes.append(KnowledgeNode(id=skill_id, label=skill, type="skill"))
            edges.append(KnowledgeEdge(source=document_id, target=skill_id, type="MENTIONS_SKILL"))

        for project in project_names:
            project_id = f"project:{project.lower().replace(' ', '-')}"
            nodes.append(KnowledgeNode(id=project_id, label=project, type="project"))
            edges.append(KnowledgeEdge(source=document_id, target=project_id, type="CONTAINS_PROJECT"))
            for skill in skills:
                if skill in SKILL_KEYWORDS:
                    edges.append(
                        KnowledgeEdge(
                            source=project_id,
                            target=f"skill:{skill}",
                            type="USES_SKILL",
                        )
                    )

        return KnowledgeGraph(nodes=nodes, edges=edges)


def extract_project_names(text: str) -> list[str]:
    matches = re.findall(r"(?:project|built|created|developed)\s+([A-Z][A-Za-z0-9 ]{2,40})", text)
    cleaned = [" ".join(match.split()[:5]).strip() for match in matches]
    return sorted({item for item in cleaned if item})

