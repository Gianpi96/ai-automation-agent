from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum


class AgentStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict
    result: str | None = None
    duration_ms: int = 0
    success: bool = True


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    context: dict | None = None


class AgentResult(BaseModel):
    answer: str
    tools_used: list[str]
    iterations: int
    confidence: float = Field(ge=0.0, le=1.0)
    status: AgentStatus = AgentStatus.COMPLETED
    tool_calls: list[ToolCall] = []
    total_duration_ms: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StepLog(BaseModel):
    iteration: int
    thought: str = ""
    action: str | None = None
    action_input: dict | None = None
    observation: str | None = None
    is_final: bool = False
