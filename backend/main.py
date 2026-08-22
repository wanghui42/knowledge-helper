# -*- coding: utf-8 -*-
"""FastAPI 入口：REST + SSE（文档第 10 节 API）。"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
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
    logger.warning("未配置 OPENAI_API_KEY，使用确定性降级模式（无 LLM）；配置后自动切换 OpenAI Agents SDK。")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LLM 一对一自适应教学系统", version="0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Schemas ----------------

class StartRequest(BaseModel):
    goal: str = Field(default="学习微积分", description="学习目标")
    subject: str = Field(default="math")


class AnswerRequest(BaseModel):
    question_id: str
    answer: int = Field(ge=0, le=3)


class MessageRequest(BaseModel):
    message: str


# ---------------- API ----------------

@app.post("/api/learning/start")
def start(req: StartRequest, db: DbSession = Depends(get_db)):
    """创建 session + 返回第一道诊断题。"""
    session = loop.start_session(db, req.goal, req.subject)
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
    """session 状态 + 当前题（如果存在）。"""
    try:
        session = get_or_404(db, session_id)
    except KeyError:
        raise HTTPException(404, "session not found")
    question_dict = None
    if session.current_question_id:
        q = db.get(Question, session.current_question_id)
        if q is not None:
            question_dict = _qdict(q)
    return {
        "session_id": session.id,
        "stage": session.stage,
        "goal": session.goal,
        "subject": session.subject,
        "current_node_id": session.current_node_id,
        "current_question_id": session.current_question_id,
        "question": question_dict,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@app.get("/api/learning/{session_id}/map")
def get_map(session_id: str, db: DbSession = Depends(get_db)):
    """知识地图（Mermaid 数据接口，文档第 16 节）。"""
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(404, "session not found")

    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == session.subject).all()
    edges = db.query(KnowledgeEdge).filter(
        (KnowledgeEdge.source_id.in_([n.id for n in nodes])) |
        (KnowledgeEdge.target_id.in_([n.id for n in nodes]))
    ).all()

    states = {
        s.node_id: s for s in
        db.query(LearnerState).filter(LearnerState.session_id == session_id).all()
    }
    node_list = []
    for n in nodes:
        st = states.get(n.id)
        # 只有有答题证据（evidence_count > 0）的节点才算已测；
        # 否则 mastery=None，状态为未测（灰色 none）
        mastery = st.overall if st and st.evidence_count > 0 else None
        status = "none" if mastery is None else mastery_level(mastery)
        node_list.append({
            "id": n.id, "title": n.title, "description": n.description,
            "difficulty": n.difficulty, "importance": n.importance,
            "mastery": mastery, "status": status,
        })
    edge_list = [
        {"source": e.source_id, "target": e.target_id, "relation": e.relation}
        for e in edges
    ]
    return {"nodes": node_list, "edges": edge_list}


@app.post("/api/learning/{session_id}/answer")
def answer(session_id: str, req: AnswerRequest, db: DbSession = Depends(get_db)):
    """提交诊断/后测答案。"""
    try:
        session = get_or_404(db, session_id)
    except KeyError:
        raise HTTPException(404, "session not found")
    try:
        result = loop.submit_answer(db, session, req.question_id, req.answer)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    return {
        "correct": result["correct"],
        "stage": result["stage"],
        "question": result["question"],
    }


@app.post("/api/learning/{session_id}/message")
async def message(session_id: str, req: MessageRequest, db: DbSession = Depends(get_db)):
    """教学对话（SSE 流式）。"""
    try:
        session = get_or_404(db, session_id)
    except KeyError:
        raise HTTPException(404, "session not found")
    try:
        result = loop.tutor_message(db, session, req.message)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    async def event_stream():
        content = result["content"]
        # 模拟流式分块
        chunk_size = 24
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'type': 'done', 'intent': result['intent'], 'node_id': result['node_id']}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/learning/{session_id}/start-assessment")
def start_assessment(session_id: str, db: DbSession = Depends(get_db)):
    """启动后测。"""
    try:
        session = get_or_404(db, session_id)
    except KeyError:
        raise HTTPException(404, "session not found")
    try:
        q = loop.start_assessment(db, session)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"stage": session.stage, "question": _qdict(q) if q else None}


@app.get("/api/learning/{session_id}/progress")
def progress(session_id: str, db: DbSession = Depends(get_db)):
    """学习进度：当前节点、掌握度、各节点状态。"""
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(404, "session not found")

    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == session.subject).all()
    states = {
        s.node_id: s for s in
        db.query(LearnerState).filter(LearnerState.session_id == session_id).all()
    }
    node_progress = []
    for n in nodes:
        st = states.get(n.id)
        node_progress.append({
            "node_id": n.id,
            "title": n.title,
            "conceptual": st.conceptual if st else 0.0,
            "procedural": st.procedural if st else 0.0,
            "transfer": st.transfer if st else 0.0,
            "overall": st.overall if st else 0.0,
            "evidence_count": st.evidence_count if st else 0,
            "status": mastery_level(st.overall) if st and st.evidence_count > 0 else "untested",
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
    """开发调试事件流。"""
    rows = (
        db.query(Event)
        .filter(Event.session_id == session_id)
        .order_by(Event.id.asc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "payload": json.loads(e.payload_json),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ]


@app.get("/api/learning/{session_id}/messages")
def messages(session_id: str, db: DbSession = Depends(get_db)):
    """历史教学消息。"""
    rows = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.asc())
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "node_id": m.node_id}
        for m in rows
    ]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_mode": LLM_MODE if LLM_MODE != "auto" else ("openai" if config.OPENAI_API_KEY else "deterministic"),
        "openai_configured": bool(config.OPENAI_API_KEY),
    }


def _qdict(q) -> dict:
    payload = json.loads(q.payload_json)
    return {
        "id": q.id,
        "node_id": q.node_id,
        "skill": q.skill,
        "type": q.type,
        "question": payload["question"],
        "options": payload["options"],
        "difficulty": q.difficulty,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
