from __future__ import annotations


class OfflineQueryRewriter:
    """Multi-query retrieval without needing an LLM call."""

    def rewrite(self, query: str, role_title: str | None = None, skills: list[str] | None = None) -> list[str]:
        skills = skills or []
        role = role_title or "target role"
        rewrites = [
            query,
            f"{query} evidence from resume projects achievements impact",
            f"{role} interview rubric answer quality technical depth {query}",
        ]
        for skill in skills[:5]:
            rewrites.append(f"{skill} experience examples responsibilities results {query}")
        return dedupe_preserve_order(rewrites)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = " ".join(value.lower().split())
        if normalized in seen:
            continue
        seen.add(normalized)
        output.append(value)
    return output

