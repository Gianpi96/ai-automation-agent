import logging
import aiofiles
from pathlib import Path
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log", ".py", ".yaml", ".yml"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

_SCHEMA = {
    "name": "read_file",
    "description": "Read the content of a local text file. Supports .txt, .md, .json, .csv, .log, .py, .yaml files.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the file to read",
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters to return (default 4000)",
                "default": 4000,
            },
        },
        "required": ["file_path"],
    },
}


@register_tool("read_file", _SCHEMA)
async def read_file(file_path: str, max_chars: int = 4000) -> str:
    logger.info("read_file path=%r", file_path)
    path = Path(file_path)

    if not path.exists():
        return f"Error: File not found: {file_path}"

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return f"Error: File type '{path.suffix}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    if path.stat().st_size > MAX_FILE_SIZE:
        return f"Error: File too large (max 1MB)"

    try:
        async with aiofiles.open(path, mode="r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... [truncated at {max_chars} chars]"
        return content
    except Exception as e:
        logger.error("read_file error: %s", e)
        return f"Error reading file: {e}"
