# -*- coding: utf-8 -*-
"""FastAPI 入口：REST + SSE。"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

import config
from database import Base, engine, get_db
from models.enums import mastery_level
from models.event import Event
from models.knowledge import KnowledgeEdge, KnowledgeNode
from models.learner import LearnerState
from models.message import Message
from models.question import Question
from models.session import LearningSession
from orchestration import learning_loop as loop
from orchestration.state_manager import get_or_404

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adaptive-tutor")

LLM_MODE = config.LLM_PROVIDER
if not config.OPENAI_API_KEY and LLM_MODE != "deterministic":
    logger.warning("未配置 OPENAI_API_KEY，使用确定性降级模式。")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LLM 一对一自适应教学系统", version="0.2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    goal: str = Field(default="学习微积分", min_length=1, max_length=500)
    subject: str = Field(default="math", min_length=1, max_length=64)


class AnswerRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    answer: int = Field(ge=0, le=3)


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


@app.post("/api/learning/start")
def start(req: StartRequest, db: DbSession = Depends(get_db)):
    session = loop.start_session(db, req.goal.strip(), req.subject.strip())
    question = loop.next_diagnostic_question(db, session)
    db.refresh(session)
    return {
        "session_id": session.id,
        "stage": session.stage,
        "goal": session.goal,
        "subject": session.subject,
        "question": _qdict(question) if question else None,
    }


@app.get("/api/learning/{session_id}")
def get_session(session_id: str, db: DbSession = Depends(get_db)):
    try:
        session = get_or_404(db, session_id)
    except KeyError:
        raise HTTPException(404, "session not found")

    question = db.get(Question, session.current_question_id) if session.current_question_id else None
    return {
        "session_id": session.id,
        "stage": session.stage,
        "goal": session.goal,
        "subject": session.subject,
        "current_node_id": session.current_node_id,
        "current_question_id": session.current_question_id,
        "question": _qdict(question) if question else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@app.get("/api/learning/{session_id}/map")
def get_map(session_id: str, db: DbSession = Depends(get_db)):
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(404, "session not found")

    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == session.subject).all()
    node_ids = {node.id for node in nodes}
    edges = db.query(KnowledgeEdge).filter(
        KnowledgeEdge.source_id.in_(node_ids),
        KnowledgeEdge.target_id.in_(node_ids),
    ).all()
    states = {
        state.node_id: state
        for state in db.query(LearnerState).filter(LearnerState.session_id == session_id).all()
    }

    node_list = []
    for node in nodes:
        state = states.get(node.id)
        mastery = state.overall if state and state.evidence_count > 0 else None
        node_list.append({
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "difficulty": node.difficulty,
            "importance": node.importance,
            "mastery": mastery,
            "status": "none" if mastery is None else mastery_level(mastery),
        })

    return {
        "nodes": node_list,
        "edges": [
            {"source": edge.source_id, "target": edge.target_id, "relation": edge.relation}
            for edge in edges
        ],
    }


@app.post("/api/learning/{session_id}/answer")
def answer(session_id: str, req: AnswerRequest, db: DbSession = Depends(get_db)):
    try:
        session = get_or_404(db, session_id)
        result = loop.submit_answer(db, session, req.question_id, req.answer)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {
        "correct": result["correct"],
        "stage": result["stage"],
        "question": result["question"],
    }


@app.post("/api/learning/{session_id}/message")
async def message(session_id: str, req: MessageRequest, db: DbSession = Depends(get_db)):
    try:
        session = get_or_404(db, session_id)
        # TutorAgent 当前接口为同步调用；在线程池中执行，避免在 async endpoint 中嵌套 asyncio.run。
        result = await asyncio.to_thread(loop.tutor_message, db, session, req.message.strip())
    except KeyError:
        raise HTTPException(404, "session not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.exception("tutor message failed")
        raise HTTPException(502, f"tutor generation failed: {exc}")

    async def event_stream():
        content = result["content"]
        chunk_size = 48
        for start in range(0, len(content), chunk_size):
            chunk = content[start:start + chunk_size]
            yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'type': 'done', 'intent': result['intent'], 'node_id': result['node_id']}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/api/learning/{session_id}/start-assessment")
def start_assessment(session_id: str, db: DbSession = Depends(get_db)):
    try:
        session = get_or_404(db, session_id)
        question = loop.start_assessment(db, session)
    except KeyError:
        raise HTTPException(404, "session not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"stage": session.stage, "question": _qdict(question) if question else None}


@app.get("/api/learning/{session_id}/progress")
def progress(session_id: str, db: DbSession = Depends(get_db)):
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(404, "session not found")

    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == session.subject).all()
    states = {
        state.node_id: state
        for state in db.query(LearnerState).filter(LearnerState.session_id == session_id).all()
    }
    node_progress = []
    for node in nodes:
        state = states.get(node.id)
        tested = bool(state and state.evidence_count > 0)
        node_progress.append({
            "node_id": node.id,
            "title": node.title,
            "conceptual": state.conceptual if state else 0.0,
            "procedural": state.procedural if state else 0.0,
            "transfer": state.transfer if state else 0.0,
            "overall": state.overall if state else 0.0,
            "evidence_count": state.evidence_count if state else 0,
            "status": mastery_level(state.overall) if tested else "untested",
        })

    return {
        "session_id": session.id,
        "stage": session.stage,
        "goal": session.goal,
        "current_node_id": session.current_node_id,
        "nodes": node_progress,
    }


@app.get("/api/learning/{session_id}/events")
def events(session_id: str, db: DbSession = Depends(get_db)):
    if db.get(LearningSession, session_id) is None:
        raise HTTPException(404, "session not found")
    rows = (
        db.query(Event)
        .filter(Event.session_id == session_id)
        .order_by(Event.id.asc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "payload": json.loads(event.payload_json),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for event in rows
    ]


@app.get("/api/learning/{session_id}/messages")
def messages(session_id: str, db: DbSession = Depends(get_db)):
    if db.get(LearningSession, session_id) is None:
        raise HTTPException(404, "session not found")
    rows = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.asc())
        .all()
    )
    return [
        {"role": message.role, "content": message.content, "node_id": message.node_id}
        for message in rows
    ]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_mode": LLM_MODE if LLM_MODE != "auto" else ("openai" if config.OPENAI_API_KEY else "deterministic"),
        "openai_configured": bool(config.OPENAI_API_KEY),
    }


def _qdict(question: Question | None) -> dict | None:
    if question is None:
        return None
    payload = json.loads(question.payload_json)
    return {
        "id": question.id,
        "node_id": question.node_id,
        "skill": question.skill,
        "type": question.type,
        "question": payload["question"],
        "options": payload["options"],
        "difficulty": question.difficulty,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
