# INFRASTRUCTURE
import requests

SEARXNG_URL = "http://localhost:8080/search"
MAX_RESULTS = 20


# ORCHESTRATOR
def search_web_workflow(query: str, category: str) -> dict:
    raw_results = fetch_search_results(query, category)
    return format_results(query, category, raw_results)


# FUNCTIONS

# Fetch raw search results from SearXNG API
def fetch_search_results(query: str, category: str) -> list:
    params = {
        "q": query,
        "format": "json",
        "categories": category
    }
    response = requests.get(SEARXNG_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])[:MAX_RESULTS]


# Transform raw results into structured output
def format_results(query: str, category: str, raw_results: list) -> dict:
    return {
        "query": query,
        "category": category,
        "total_results": len(raw_results),
        "results": [
            {
                "title": item.get("title", "No title"),
                "url": item.get("url", ""),
                "content": item.get("content", "")
            }
            for item in raw_results
        ]
    }
