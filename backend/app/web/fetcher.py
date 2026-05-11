from __future__ import annotations

from html.parser import HTMLParser

import httpx

from app.core.config import settings
from app.web.models import WebSource
from app.web.search import user_agent


class SourceFetcher:
    async def fetch(self, source: WebSource) -> WebSource:
        if not settings.web_fetch_pages:
            return source
        try:
            async with httpx.AsyncClient(
                timeout=settings.web_request_timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": user_agent()},
            ) as client:
                response = await client.get(source.url)
                response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type or "text/plain" in content_type:
                source.fetched_text = extract_visible_text(response.text)[:12000]
        except Exception:
            source.fetched_text = ""
        return source


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)


def extract_visible_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    return " ".join(parser.parts)

