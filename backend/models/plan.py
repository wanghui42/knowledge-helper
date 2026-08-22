# -*- coding: utf-8 -*-
"""plans 表：学习计划。"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    current_node_id: Mapped[str] = mapped_column(String(64), index=True)
    plan_json: Mapped[str] = mapped_column(Text)  # {"current_node","next_nodes":[],"rationale":[]}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
