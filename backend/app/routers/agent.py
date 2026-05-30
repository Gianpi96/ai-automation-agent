import logging
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from app.models.agent import AgentRequest, AgentResult
from app.agents.react_agent import run_react_loop
from app.tools import list_tools, get_tool_schemas
from app.services.stats import tracker, ExecutionRecord

router = APIRouter(prefix="/api/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=AgentResult)
async def run_agent(request: AgentRequest) -> AgentResult:
    started_at = datetime.now(UTC)
    try:
        result = await run_react_loop(request.query, request.context)
        tracker.record(ExecutionRecord(
            agent_id="react-agent",
            agent_name="Agente ReAct",
            status=result.status.value,
            started_at=started_at,
            duration_ms=result.total_duration_ms,
            iterations=result.iterations,
            tools_used=result.tools_used,
        ))
        return result
    except Exception as e:
        tracker.record(ExecutionRecord(
            agent_id="react-agent",
            agent_name="Agente ReAct",
            status="failed",
            started_at=started_at,
            duration_ms=0,
            iterations=0,
            tools_used=[],
            error=str(e),
        ))
        logger.error("Agent run failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_available_tools() -> dict:
    return {"tools": list_tools(), "schemas": get_tool_schemas()}


@router.get("/stats")
async def get_stats() -> dict:
    return tracker.get_stats()


@router.get("/logs")
async def get_logs() -> list:
    return tracker.get_logs()
