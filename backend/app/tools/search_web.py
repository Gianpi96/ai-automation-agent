import logging
import asyncio
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

_SCHEMA = {
    "name": "search_web",
    "description": "Search the web for current information on a topic. Returns a list of relevant results.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (1-5)",
                "minimum": 1,
                "maximum": 5,
                "default": 3,
            },
        },
        "required": ["query"],
    },
}


@register_tool("search_web", _SCHEMA)
async def search_web(query: str, num_results: int = 3) -> str:
    """Simulated web search — replace with real search API in production."""
    logger.info("search_web query=%r num_results=%d", query, num_results)
    await asyncio.sleep(0.1)  # simulate network latency

    results = [
        {
            "title": f"Result {i + 1} for '{query}'",
            "url": f"https://example.com/result-{i + 1}",
            "snippet": (
                f"This is a simulated search result about '{query}'. "
                f"In production, integrate with DuckDuckGo, Bing, or SerpAPI. "
                f"Result number {i + 1} of {num_results}."
            ),
        }
        for i in range(min(num_results, 5))
    ]

    formatted = "\n\n".join(
        f"[{r['title']}]({r['url']})\n{r['snippet']}" for r in results
    )
    return f"Search results for '{query}':\n\n{formatted}"
