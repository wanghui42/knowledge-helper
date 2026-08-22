# -*- coding: utf-8 -*-
"""sessions 表：一次学习会话。"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def _uuid() -> str:
    return "sess_" + uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LearningSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), default="default-user")
    goal: Mapped[str] = mapped_column(String(255), default="学习微积分")
    subject: Mapped[str] = mapped_column(String(64), default="math")
    stage: Mapped[str] = mapped_column(String(32), default="INIT")
    current_node_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_question_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


# 兼容别名
Session = LearningSession
