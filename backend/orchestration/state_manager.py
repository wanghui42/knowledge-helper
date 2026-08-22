# -*- coding: utf-8 -*-
"""state_manager.py：Session 状态读写与事件记录。"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session as DbSession

from models.enums import SessionStage
from models.event import Event
from models.session import LearningSession


def get_or_404(db: DbSession, session_id: str) -> LearningSession:
    session = db.get(LearningSession, session_id)
    if session is None:
        raise KeyError(f"session {session_id} not found")
    return session


def set_stage(db: DbSession, session: LearningSession, stage: SessionStage | str) -> None:
    session.stage = stage if isinstance(stage, str) else stage.value
    db.flush()


def log_event(
    db: DbSession,
    session_id: str,
    event_type: str,
    payload: dict | None = None,
) -> Event:
    ev = Event(
        session_id=session_id,
        event_type=event_type,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
    )
    db.add(ev)
    db.flush()
    return ev
