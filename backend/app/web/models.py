from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WebSource:
    title: str
    url: str
    snippet: str
    provider: str
    fetched_text: str = ""
    score: float = 0.0


@dataclass
class ClaimCheck:
    claim: str
    verdict: str
    confidence: float
    explanation: str
    sources: list[WebSource] = field(default_factory=list)


@dataclass
class VerificationReport:
    enabled: bool
    provider: str
    overall_verdict: str
    overall_score: float
    summary: str
    corrected_answer: str
    claims: list[ClaimCheck] = field(default_factory=list)
    sources: list[WebSource] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

