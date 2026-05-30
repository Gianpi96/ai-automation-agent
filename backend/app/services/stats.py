from datetime import datetime, UTC
from dataclasses import dataclass, field


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
    def __init__(self):
        self._executions: list[ExecutionRecord] = []

    def record(self, record: ExecutionRecord) -> None:
        self._executions.append(record)

    def get_stats(self) -> dict:
        now = datetime.now(UTC)
        today = now.date()
        today_runs = [
            e for e in self._executions
            if e.started_at.date() == today
        ]
        completed = [e for e in today_runs if e.status == "completed"]
        total = len(today_runs)
        success_rate = round(len(completed) / total, 2) if total else 0.0
        # estimate: each run saves ~3 minutes of manual work
        time_saved = total * 3
        active_agents = len({e.agent_id for e in today_runs if e.status == "completed"})
        return {
            "processedToday": total,
            "timeSavedMinutes": time_saved,
            "successRate": success_rate,
            "activeAgents": active_agents,
        }

    def get_logs(self, limit: int = 20) -> list[dict]:
        recent = sorted(self._executions, key=lambda e: e.started_at, reverse=True)[:limit]
        return [
            {
                "id": f"log_{i}",
                "agentId": e.agent_id,
                "agentName": e.agent_name,
                "status": e.status,
                "startedAt": e.started_at.isoformat(),
                "duration": e.duration_ms,
                "iterations": e.iterations,
                "toolsUsed": e.tools_used,
                "error": e.error,
            }
            for i, e in enumerate(recent)
        ]


tracker = StatsTracker()
