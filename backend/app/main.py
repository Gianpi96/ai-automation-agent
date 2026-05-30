import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import agent, documents, email_router, websocket

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

app.include_router(agent.router)
app.include_router(documents.router)
app.include_router(email_router.router)
app.include_router(websocket.router)


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "AI Automation Agent", "version": "1.0.0"}


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
