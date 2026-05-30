import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

_registry: dict[str, tuple[Callable, dict]] = {}


def register_tool(name: str, schema: dict):
    """Decorator to register a tool with its JSON schema."""
    def decorator(fn: Callable) -> Callable:
        _registry[name] = (fn, schema)
        logger.debug("Registered tool: %s", name)
        return fn
    return decorator


async def execute_tool(name: str, arguments: dict) -> Any:
    if name not in _registry:
        raise ValueError(f"Unknown tool: {name}")
    fn, _ = _registry[name]
    return await fn(**arguments)


def get_tool_schemas() -> list[dict]:
    return [
        {"type": "function", "function": schema}
        for _, schema in _registry.values()
    ]


def list_tools() -> list[str]:
    return list(_registry.keys())
