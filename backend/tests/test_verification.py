import asyncio

from app.web.models import WebSource
from app.web.verification import AnswerVerificationService, extract_claims


class FakeSearchClient:
    provider = "fake"

    async def search(self, query: str, max_results: int) -> list[WebSource]:
        return [
            WebSource(
                title="Angular overview",
                url="https://angular.dev/overview",
                snippet="Angular is a web framework that uses components and templates.",
                provider=self.provider,
                fetched_text=(
                    "Angular is a web framework for building scalable web applications. "
                    "Angular applications are built with components and templates."
                ),
            )
        ]


class FakeFetcher:
    async def fetch(self, source: WebSource) -> WebSource:
        return source


def test_extract_claims_skips_short_fragments() -> None:
    claims = extract_claims("Yes. Angular uses components to build web applications.")
    assert claims == ["Angular uses components to build web applications."]


def test_verification_marks_supported_claim() -> None:
    service = AnswerVerificationService(search_client=FakeSearchClient(), fetcher=FakeFetcher())

    report = asyncio.run(
        service.verify_answer(
            answer="Angular uses components and templates to build web applications.",
            question="What is Angular?",
        )
    )

    assert report.provider == "fake"
    assert report.claims
    assert report.claims[0].verdict in {"verified", "partially_verified"}
    assert report.corrected_answer
