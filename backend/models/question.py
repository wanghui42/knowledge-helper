# -*- coding: utf-8 -*-
"""questions / attempts 表：题目与答题记录。"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_nodes.id"), index=True)
    skill: Mapped[str] = mapped_column(String(32), default="concept")  # Concept | Procedure | Transfer
    type: Mapped[str] = mapped_column(String(32), default="mcq")  # 四选一
    payload_json: Mapped[str] = mapped_column(Text)  # {"question", "options":[...], "correct_index"}
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), index=True)
    question_id: Mapped[str] = mapped_column(String(64), ForeignKey("questions.id"), index=True)
    answer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
