import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.base import init_db
from app.routers import agent, documents, email_router, websocket
from app.routers.auth import router as auth_router, verify_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Automation Agent starting up...")
    import app.tools  # noqa: F401 — trigger tool registration
    logger.info("Tools registered: %s", app.tools.list_tools())
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("AI Automation Agent shutting down...")


app = FastAPI(
    title="AI Automation Agent",
    description="ReAct agent with Groq LLM, document processing, and email automation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes
app.include_router(auth_router)

# Protected routes (require JWT)
protected = {"dependencies": [Depends(verify_token)]}
app.include_router(agent.router, **protected)
app.include_router(documents.router, **protected)
app.include_router(email_router.router, **protected)
app.include_router(websocket.router)  # WS handles its own auth


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "AI Automation Agent", "version": "1.0.0"}


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
