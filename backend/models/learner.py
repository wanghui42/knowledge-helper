# -*- coding: utf-8 -*-
"""learner_states 表：每个会话在每个节点的掌握状态。"""
from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LearnerState(Base):
    __tablename__ = "learner_states"
    __table_args__ = (UniqueConstraint("session_id", "node_id", name="uq_session_node"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_nodes.id"), index=True)
    conceptual: Mapped[float] = mapped_column(Float, default=0.0)
    procedural: Mapped[float] = mapped_column(Float, default=0.0)
    transfer: Mapped[float] = mapped_column(Float, default=0.0)
    overall: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def mastery(self) -> float:
        return self.overall
