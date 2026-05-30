import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Force test environment settings BEFORE importing app
os.environ.setdefault("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
