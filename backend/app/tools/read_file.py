import logging
import aiofiles
from pathlib import Path
from app.config import settings
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log", ".py", ".yaml", ".yml"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

_SCHEMA = {
    "name": "read_file",
    "description": (
        "Read the content of a text file from the configured watched folder. "
        f"Supported: .txt, .md, .json, .csv, .log, .py, .yaml files. "
        "Pass just the filename (e.g. 'notes.txt') or a relative path."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Filename or relative path inside the watched folder",
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
    watched = Path(settings.watched_folder)
    # Resolve relative to watched folder, prevent path traversal
    try:
        target = (watched / file_path).resolve()
        target.relative_to(watched.resolve())  # raises ValueError if outside
    except ValueError:
        return f"Errore: accesso negato — il file deve essere dentro {watched}"

    logger.info("read_file path=%s", target)

    if not target.exists():
        # List available files as hint
        available = [f.name for f in watched.rglob("*") if f.is_file() and f.suffix in ALLOWED_EXTENSIONS][:10]
        hint = f"File disponibili in {watched}: {', '.join(available) or 'nessuno'}"
        return f"Errore: file non trovato: {file_path}\n{hint}"

    if target.suffix.lower() not in ALLOWED_EXTENSIONS:
        return f"Errore: estensione '{target.suffix}' non supportata. Supportate: {', '.join(ALLOWED_EXTENSIONS)}"

    if target.stat().st_size > MAX_FILE_SIZE:
        return "Errore: file troppo grande (max 1MB)"

    try:
        async with aiofiles.open(target, mode="r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... [troncato a {max_chars} caratteri]"
        return content
    except Exception as e:
        logger.error("read_file error: %s", e)
        return f"Errore lettura file: {e}"
