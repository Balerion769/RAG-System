from __future__ import annotations

import re
from collections import Counter

from app.core.config import settings
from app.web.fetcher import SourceFetcher
from app.web.models import ClaimCheck, VerificationReport, WebSource
from app.web.search import WebSearchClient, get_search_client


STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "have",
    "has",
    "had",
    "was",
    "were",
    "are",
    "you",
    "your",
    "our",
    "their",
    "about",
    "into",
    "using",
    "used",
    "will",
    "can",
    "also",
    "based",
    "because",
    "project",
    "answer",
}

VERDICT_SCORE = {
    "verified": 92.0,
    "partially_verified": 68.0,
    "needs_review": 45.0,
    "not_verified": 25.0,
    "no_sources": 0.0,
}


class AnswerVerificationService:
    def __init__(
        self,
        search_client: WebSearchClient | None = None,
        fetcher: SourceFetcher | None = None,
    ) -> None:
        self.search_client = search_client or get_search_client()
        self.fetcher = fetcher or SourceFetcher()

    async def verify_answer(
        self,
        answer: str,
        question: str | None = None,
        role_title: str | None = None,
        max_claims: int = 5,
    ) -> VerificationReport:
        if not settings.web_search_enabled:
            return VerificationReport(
                enabled=False,
                provider=self.search_client.provider,
                overall_verdict="disabled",
                overall_score=0.0,
                summary="Web verification is disabled by configuration.",
                corrected_answer="",
                limitations=["Set WEB_SEARCH_ENABLED=true to use online verification."],
            )

        claims = extract_claims(answer, max_claims=max_claims)
        if not claims:
            return VerificationReport(
                enabled=True,
                provider=self.search_client.provider,
                overall_verdict="not_verified",
                overall_score=0.0,
                summary="No concrete factual claims were found to verify.",
                corrected_answer="Add a specific factual or technical claim before checking sources.",
                limitations=["Short or purely personal answers may need resume evidence rather than web evidence."],
            )

        claim_checks: list[ClaimCheck] = []
        source_lookup: dict[str, WebSource] = {}

        for claim in claims:
            query = build_search_query(claim, question=question, role_title=role_title)
            try:
                sources = await self.search_client.search(query, max_results=settings.web_max_results)
            except Exception:
                sources = []

            enriched_sources = []
            for source in sources:
                enriched = await self.fetcher.fetch(source)
                enriched_sources.append(enriched)
                source_lookup[enriched.url] = enriched

            claim_checks.append(check_claim_against_sources(claim, enriched_sources))

        overall_score = round(
            sum(VERDICT_SCORE.get(check.verdict, 0.0) for check in claim_checks) / max(1, len(claim_checks)),
            1,
        )
        overall_verdict = overall_verdict_from_score(overall_score, claim_checks)
        sources = sorted(source_lookup.values(), key=lambda item: item.score, reverse=True)[: settings.web_max_results]

        return VerificationReport(
            enabled=True,
            provider=self.search_client.provider,
            overall_verdict=overall_verdict,
            overall_score=overall_score,
            summary=build_summary(overall_verdict, claim_checks),
            corrected_answer=build_corrected_answer(claim_checks),
            claims=claim_checks,
            sources=sources,
            limitations=[
                "Web verification can confirm public technical facts, docs, and current information.",
                "Private resume claims still require uploaded resume, project links, certificates, or portfolio evidence.",
                "If sources do not prove a claim, the system marks it not verified instead of guessing.",
            ],
        )


def extract_claims(answer: str, max_claims: int = 5) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", answer.strip())
    claims: list[str] = []
    for part in parts:
        cleaned = " ".join(part.strip(" -\t\r\n").split())
        if len(cleaned.split()) < 5:
            continue
        if cleaned.lower().startswith(("i think", "i feel", "maybe", "probably")):
            continue
        claims.append(cleaned[:420])
    if not claims and answer.strip():
        claims.append(" ".join(answer.strip().split())[:420])
    return claims[:max_claims]


def build_search_query(claim: str, question: str | None = None, role_title: str | None = None) -> str:
    hints = " ".join(item for item in [role_title, question] if item)
    claim_tokens = " ".join(key_terms(claim, limit=10))
    return " ".join([claim_tokens, hints]).strip() or claim


def check_claim_against_sources(claim: str, sources: list[WebSource]) -> ClaimCheck:
    if not sources:
        return ClaimCheck(
            claim=claim,
            verdict="no_sources",
            confidence=0.0,
            explanation="No web sources were returned for this claim.",
            sources=[],
        )

    claim_terms = set(key_terms(claim))
    scored_sources = []
    for source in sources:
        text = " ".join([source.title, source.snippet, source.fetched_text])
        source_terms = set(key_terms(text, limit=400))
        source.score = overlap_score(claim_terms, source_terms)
        scored_sources.append(source)

    ranked_sources = sorted(scored_sources, key=lambda item: item.score, reverse=True)
    best_score = ranked_sources[0].score if ranked_sources else 0.0
    verdict = verdict_from_overlap(best_score, claim, ranked_sources)
    explanation = explanation_for_verdict(verdict, best_score)

    return ClaimCheck(
        claim=claim,
        verdict=verdict,
        confidence=round(min(1.0, best_score), 2),
        explanation=explanation,
        sources=ranked_sources[:3],
    )


def key_terms(text: str, limit: int = 80) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9+#.:-]+", text.lower())
    useful = [token.strip(".:-") for token in tokens if len(token.strip(".:-")) > 2]
    useful = [token for token in useful if token and token not in STOPWORDS]
    counts = Counter(useful)
    return [token for token, _ in counts.most_common(limit)]


def overlap_score(claim_terms: set[str], source_terms: set[str]) -> float:
    if not claim_terms or not source_terms:
        return 0.0
    return len(claim_terms & source_terms) / len(claim_terms)


def verdict_from_overlap(score: float, claim: str, sources: list[WebSource]) -> str:
    source_text = " ".join(
        " ".join([source.title, source.snippet, source.fetched_text]).lower() for source in sources[:2]
    )
    claim_lower = claim.lower()
    review_signal = any(signal in source_text for signal in ["deprecated", "no longer", "not recommended"])
    if review_signal and not any(signal in claim_lower for signal in ["deprecated", "no longer", "not recommended"]):
        return "needs_review"
    if score >= 0.62:
        return "verified"
    if score >= 0.35:
        return "partially_verified"
    return "not_verified"


def explanation_for_verdict(verdict: str, score: float) -> str:
    if verdict == "verified":
        return f"Strong matching public sources were found for this claim (match {score:.2f})."
    if verdict == "partially_verified":
        return f"Some public evidence matched, but the claim needs more precise support (match {score:.2f})."
    if verdict == "needs_review":
        return "Sources contain caution/deprecation language, so this claim should be reviewed carefully."
    if verdict == "no_sources":
        return "No sources were available for verification."
    return f"The returned sources did not prove this claim (match {score:.2f})."


def overall_verdict_from_score(score: float, checks: list[ClaimCheck]) -> str:
    if not checks or all(check.verdict == "no_sources" for check in checks):
        return "no_sources"
    if any(check.verdict == "needs_review" for check in checks):
        return "needs_review"
    if score >= 80:
        return "verified"
    if score >= 55:
        return "partially_verified"
    return "not_verified"


def build_summary(verdict: str, checks: list[ClaimCheck]) -> str:
    counts = Counter(check.verdict for check in checks)
    if verdict == "verified":
        return "The answer is mostly supported by public sources."
    if verdict == "partially_verified":
        return (
            "The answer has some source support, but a few claims need clearer citations or more precise wording. "
            f"Claims: {dict(counts)}"
        )
    if verdict == "needs_review":
        return "At least one claim needs review because sources contain caution or deprecation signals."
    if verdict == "no_sources":
        return "No usable web sources were found, so the answer was not verified online."
    return "The available web sources did not prove the answer. Treat it as unverified until cited."


def build_corrected_answer(checks: list[ClaimCheck]) -> str:
    supported_sentences: list[str] = []
    for check in checks:
        if check.verdict not in {"verified", "partially_verified", "needs_review"}:
            continue
        sentence = best_source_sentence(check.claim, check.sources)
        if sentence:
            supported_sentences.append(sentence)

    if not supported_sentences:
        return (
            "I could not build a source-backed corrected answer. Add official docs, project links, "
            "or more specific claims, then verify again."
        )
    return " ".join(dedupe_preserve_order(supported_sentences))[:1200]


def best_source_sentence(claim: str, sources: list[WebSource]) -> str:
    claim_terms = set(key_terms(claim))
    candidates: list[tuple[float, str]] = []
    for index, source in enumerate(sources, start=1):
        text = " ".join([source.snippet, source.fetched_text])
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences[:40]:
            cleaned = " ".join(sentence.split())
            if len(cleaned.split()) < 6 or len(cleaned) > 260:
                continue
            score = overlap_score(claim_terms, set(key_terms(cleaned)))
            if score > 0:
                candidates.append((score, f"{cleaned} [{index}]"))
    if not candidates:
        return ""
    return max(candidates, key=lambda item: item[0])[1]


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        output.append(value)
    return output

