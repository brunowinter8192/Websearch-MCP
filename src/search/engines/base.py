# INFRASTRUCTURE
from abc import ABC, abstractmethod

from src.search.result import SearchResult


# Abstract base class for all search engine implementations
class BaseEngine(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        ...

    # Default: delegates to search(); every engine returns (results, empty_reason, diagnosis) — diagnosis is a raw-facts dict behind a non-None empty_reason, or None
    async def search_with_reason(self, query: str, language: str = "en", max_results: int = 10) -> tuple[list[SearchResult], str | None, dict | None]:
        results = await self.search(query, language, max_results)
        return results, None, None
