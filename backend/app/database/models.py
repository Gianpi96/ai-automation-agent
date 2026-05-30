import json
from datetime import datetime, UTC
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(50))
    agent_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    iterations: Mapped[int] = mapped_column(Integer, default=1)
    tools_used_json: Mapped[str] = mapped_column(Text, default="[]")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def tools_used(self) -> list[str]:
        return json.loads(self.tools_used_json)

    @tools_used.setter
    def tools_used(self, value: list[str]) -> None:
        self.tools_used_json = json.dumps(value)

    def to_dict(self, index: int = 0) -> dict:
        return {
            "id": f"log_{self.id}",
            "agentId": self.agent_id,
            "agentName": self.agent_name,
            "status": self.status,
            "startedAt": self.started_at.isoformat(),
            "duration": self.duration_ms,
            "iterations": self.iterations,
            "toolsUsed": self.tools_used,
            "error": self.error,
        }
