from __future__ import annotations

from app.models.domain import DocumentChunk, RetrievedChunk


class ParentChildExpander:
    def expand(
        self,
        results: list[RetrievedChunk],
        parents: dict[str, DocumentChunk],
        max_parent_chars: int = 1800,
    ) -> list[RetrievedChunk]:
        for result in results:
            parent_id = result.chunk.parent_id
            parent = parents.get(parent_id or "")
            if parent:
                result.expanded_text = parent.text[:max_parent_chars]
            else:
                result.expanded_text = result.chunk.text
        return results

