import logging
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
    logger.info("search_web query=%r num_results=%d", query, num_results)
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=min(num_results, 5))
        if not results:
            return f"Nessun risultato trovato per '{query}'."
        formatted = "\n\n".join(
            f"**{r['title']}**\n{r['href']}\n{r['body']}" for r in results
        )
        return f"Risultati ricerca per '{query}':\n\n{formatted}"
    except Exception as e:
        logger.error("search_web error: %s", e)
        return f"Errore durante la ricerca: {e}"
