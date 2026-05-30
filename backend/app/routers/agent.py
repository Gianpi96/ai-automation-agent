import logging
from fastapi import APIRouter, HTTPException
from app.models.agent import AgentRequest, AgentResult
from app.agents.react_agent import run_react_loop
from app.tools import list_tools, get_tool_schemas

router = APIRouter(prefix="/api/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=AgentResult)
async def run_agent(request: AgentRequest) -> AgentResult:
    """Run the ReAct agent loop on a query."""
    logger.info("Agent run request: query=%r", request.query)
    try:
        result = await run_react_loop(request.query, request.context)
        return result
    except Exception as e:
        logger.error("Agent run failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_available_tools() -> dict:
    """List all registered tools with their schemas."""
    return {
        "tools": list_tools(),
        "schemas": get_tool_schemas(),
    }
