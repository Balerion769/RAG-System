from __future__ import annotations

import json
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.core.config import settings
from app.web.models import WebSource


class WebSearchClient:
    provider = "disabled"

    async def search(self, query: str, max_results: int) -> list[WebSource]:
        return []


class DuckDuckGoSearchClient(WebSearchClient):
    provider = "duckduckgo"
    endpoint = "https://duckduckgo.com/html/"

    async def search(self, query: str, max_results: int) -> list[WebSource]:
        async with httpx.AsyncClient(
            timeout=settings.web_request_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": user_agent()},
        ) as client:
            response = await client.get(self.endpoint, params={"q": query})
            response.raise_for_status()

        parser = DuckDuckGoHtmlParser()
        parser.feed(response.text)
        return parser.results[:max_results]


class BraveSearchClient(WebSearchClient):
    provider = "brave"
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, max_results: int) -> list[WebSource]:
        if not settings.brave_search_api_key:
            return []
        async with httpx.AsyncClient(timeout=settings.web_request_timeout_seconds) as client:
            response = await client.get(
                self.endpoint,
                params={"q": query, "count": max_results},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": settings.brave_search_api_key,
                    "User-Agent": user_agent(),
                },
            )
            response.raise_for_status()
        payload = response.json()
        items = payload.get("web", {}).get("results", [])
        return [
            WebSource(
                title=item.get("title", "Untitled source"),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                provider=self.provider,
            )
            for item in items
            if item.get("url")
        ][:max_results]


class TavilySearchClient(WebSearchClient):
    provider = "tavily"
    endpoint = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int) -> list[WebSource]:
        if not settings.tavily_api_key:
            return []
        async with httpx.AsyncClient(timeout=settings.web_request_timeout_seconds) as client:
            response = await client.post(
                self.endpoint,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
                headers={"User-Agent": user_agent()},
            )
            response.raise_for_status()
        payload = response.json()
        return [
            WebSource(
                title=item.get("title", "Untitled source"),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                provider=self.provider,
            )
            for item in payload.get("results", [])
            if item.get("url")
        ][:max_results]


class DuckDuckGoHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[WebSource] = []
        self._active_link: dict | None = None
        self._active_snippet = False
        self._snippet_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = attr_map.get("class", "")
        if tag == "a" and "result__a" in classes:
            self._active_link = {"href": normalize_duckduckgo_url(attr_map.get("href", "")), "text": []}
            self._snippet_parts = []
        elif "result__snippet" in classes:
            self._active_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._active_link:
            title = " ".join(" ".join(self._active_link["text"]).split())
            url = self._active_link["href"]
            if title and url and not any(item.url == url for item in self.results):
                self.results.append(
                    WebSource(
                        title=title,
                        url=url,
                        snippet=" ".join(" ".join(self._snippet_parts).split()),
                        provider="duckduckgo",
                    )
                )
            self._active_link = None
        if self._active_snippet:
            self._active_snippet = False

    def handle_data(self, data: str) -> None:
        if self._active_link:
            self._active_link["text"].append(data)
        if self._active_snippet:
            self._snippet_parts.append(data)


def normalize_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    if url.startswith("//"):
        return "https:" + url
    return url


def get_search_client() -> WebSearchClient:
    if not settings.web_search_enabled:
        return WebSearchClient()
    provider = settings.web_search_provider.lower().strip()
    if provider == "brave":
        return BraveSearchClient()
    if provider == "tavily":
        return TavilySearchClient()
    if provider == "duckduckgo":
        return DuckDuckGoSearchClient()
    return WebSearchClient()


def user_agent() -> str:
    return "AIInterviewCoach/0.1 (+local-development)"


def sources_to_json(sources: list[WebSource]) -> str:
    return json.dumps([source.__dict__ for source in sources], ensure_ascii=True)

