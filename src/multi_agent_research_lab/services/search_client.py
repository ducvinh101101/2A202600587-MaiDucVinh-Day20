"""Search client abstraction for ResearcherAgent."""

import json
import urllib.error
import urllib.request

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily when configured, with a deterministic local fallback for offline labs.
        """

        if self.settings.tavily_api_key:
            try:
                return self._search_tavily(query, max_results)
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                return self._fallback_results(query, max_results, error=str(exc))

        return self._fallback_results(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = json.dumps(
            {
                "api_key": self.settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        return [
            SourceDocument(
                title=item.get("title") or "Untitled source",
                url=item.get("url"),
                snippet=item.get("content") or item.get("snippet") or "",
                metadata={"score": item.get("score"), "provider": "tavily"},
            )
            for item in results[:max_results]
        ]

    def _fallback_results(
        self, query: str, max_results: int, error: str | None = None
    ) -> list[SourceDocument]:
        documents = [
            SourceDocument(
                title="Local research planning note",
                snippet=(
                    "Break the question into scope, evidence, trade-offs, and final synthesis. "
                    f"Original query: {query}"
                ),
                metadata={"provider": "local-fallback", "error": error},
            ),
            SourceDocument(
                title="Local source quality checklist",
                snippet=(
                    "Prefer recent primary sources, compare at least two viewpoints, and flag claims "
                    "that need verification before writing the final answer."
                ),
                metadata={"provider": "local-fallback"},
            ),
        ]
        return documents[:max_results]
