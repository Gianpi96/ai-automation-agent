import json
import logging
from dataclasses import dataclass
from datetime import datetime, UTC, date

from sqlalchemy import select, func, cast, Date

from app.database.base import SessionLocal
from app.database.models import ExecutionLog as ExecutionLogModel

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    agent_id: str
    agent_name: str
    status: str
    started_at: datetime
    duration_ms: int
    iterations: int
    tools_used: list[str]
    error: str | None = None


class StatsTracker:
    async def record(self, record: ExecutionRecord) -> None:
        try:
            async with SessionLocal() as session:
                row = ExecutionLogModel(
                    agent_id=record.agent_id,
                    agent_name=record.agent_name,
                    status=record.status,
                    started_at=record.started_at,
                    duration_ms=record.duration_ms,
                    iterations=record.iterations,
                    tools_used_json=json.dumps(record.tools_used),
                    error=record.error,
                )
                session.add(row)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save execution record: %s", e)

    async def get_stats(self) -> dict:
        try:
            today = date.today()
            async with SessionLocal() as session:
                q = select(ExecutionLogModel).where(
                    cast(ExecutionLogModel.started_at, Date) == today
                )
                result = await session.execute(q)
                rows = result.scalars().all()

            total = len(rows)
            completed = sum(1 for r in rows if r.status == "completed")
            success_rate = round(completed / total, 2) if total else 0.0
            active_agents = len({r.agent_id for r in rows if r.status == "completed"})
            return {
                "processedToday": total,
                "timeSavedMinutes": total * 3,
                "successRate": success_rate,
                "activeAgents": active_agents,
            }
        except Exception as e:
            logger.error("get_stats DB error: %s", e)
            return {"processedToday": 0, "timeSavedMinutes": 0, "successRate": 0.0, "activeAgents": 0}

    async def get_logs(self, limit: int = 20) -> list[dict]:
        try:
            async with SessionLocal() as session:
                q = select(ExecutionLogModel).order_by(ExecutionLogModel.started_at.desc()).limit(limit)
                result = await session.execute(q)
                rows = result.scalars().all()
            return [r.to_dict(i) for i, r in enumerate(rows)]
        except Exception as e:
            logger.error("get_logs DB error: %s", e)
            return []


tracker = StatsTracker()
