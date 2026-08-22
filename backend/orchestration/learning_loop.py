# -*- coding: utf-8 -*-
"""learning_loop.py：Session 状态机编排。

状态：INIT → DIAGNOSIS → PLANNING → TEACHING → ASSESSMENT → REPLAN / COMPLETE
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DbSession

from agents.assessment import AssessmentAgent
from agents.diagnostic import DiagnosticAgent
from agents.knowledge_map import KnowledgeMapAgent
from agents.planner import PlannerAgent
from agents.tutor import TutorAgent
from models.enums import SessionStage
from models.knowledge import KnowledgeEdge, KnowledgeNode
from models.learner import LearnerState
from models.message import Message
from models.plan import Plan
from models.question import Attempt, Question
from models.session import LearningSession
from orchestration import diagnostic_engine as de
from orchestration.state_manager import log_event, set_stage
from schemas.agent import AssessmentResult
from services.scoring import apply_evidence, score_attempt

DIAGNOSIS_SKILLS = ["Concept", "Procedure", "Transfer"]
MASTERY_TARGET = 0.80


def start_session(db: DbSession, goal: str, subject: str = "math") -> LearningSession:
    """创建 session，确保知识地图存在，然后进入诊断。"""
    session = LearningSession(goal=goal, subject=subject, stage=SessionStage.INIT.value)
    db.add(session)
    db.flush()

    ensure_map(db, subject)
    log_event(db, session.id, "session.created", {"goal": goal, "subject": subject})

    # 状态行可以预创建，但 evidence_count=0 表示“未测量”。
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == subject).all()
    for node in nodes:
        db.add(LearnerState(session_id=session.id, node_id=node.id))
    db.flush()

    set_stage(db, session, SessionStage.DIAGNOSIS)
    db.commit()
    return session


def ensure_map(db: DbSession, subject: str) -> None:
    """加载知识地图；数据库已有该 subject 时复用现有版本。"""
    if db.query(KnowledgeNode).filter(KnowledgeNode.subject == subject).count() > 0:
        return

    try:
        km = KnowledgeMapAgent().run(subject, f"学习{subject}")
        raw = km.model_dump()
    except Exception:
        from seed.microcalculus import KNOWLEDGE_MAP
        raw = KNOWLEDGE_MAP

    version = raw.get("version", 1)
    node_ids = {node["id"] for node in raw["nodes"]}
    for node in raw["nodes"]:
        db.add(KnowledgeNode(
            id=node["id"],
            subject=subject,
            title=node["title"],
            description=node.get("description", ""),
            difficulty=node.get("difficulty", 0.5),
            importance=node.get("importance", 0.5),
            confidence=node.get("confidence", 1.0),
            version=version,
        ))

    for index, edge in enumerate(raw["edges"]):
        # 防止 LLM 生成悬空边进入数据库。
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            continue
        db.add(KnowledgeEdge(
            id=f"e_{subject}_{index}",
            source_id=edge["source"],
            target_id=edge["target"],
            relation=edge.get("relation", "prerequisite"),
            confidence=edge.get("confidence", 1.0),
        ))
    db.flush()


def next_diagnostic_question(db: DbSession, session: LearningSession) -> Question | None:
    """选择下一个待测节点并生成题目；满足停止条件时返回 None。"""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == session.subject).all()
    graph = de.get_graph(db)
    mastery_map = de.get_mastery_map(db, session.id)
    answered = db.query(Attempt).filter(Attempt.session_id == session.id).count()

    stop, reason = de.should_stop(db, session.id, mastery_map, graph, answered)
    if stop:
        log_event(db, session.id, "diagnosis.stopped", {"reason": reason})
        return None

    node = de.select_next_node(db, nodes, mastery_map, graph)
    if node is None:
        log_event(db, session.id, "diagnosis.stopped", {"reason": "no candidate node"})
        return None

    skill = DIAGNOSIS_SKILLS[answered % len(DIAGNOSIS_SKILLS)]
    question = DiagnosticAgent().run(
        {"id": node.id, "title": node.title, "description": node.description},
        skill,
        node.difficulty,
    )
    row = save_question(db, question)
    session.current_question_id = row.id
    log_event(db, session.id, "question.generated", {
        "question_id": row.id,
        "node_id": node.id,
        "skill": skill,
    })
    db.commit()
    return row


def save_question(db: DbSession, q) -> Question:
    """把 Agent 输出落库。"""
    existing = db.get(Question, q.id)
    payload = {
        "question": q.question,
        "options": q.options,
        "correct_index": q.correct_index,
        "verify_type": q.verify_type,
        "math_expr": q.math_expr,
        "correct_answer_expr": q.correct_answer_expr,
        "limit_at": q.limit_at,
    }
    if existing:
        existing.payload_json = json.dumps(payload, ensure_ascii=False)
        existing.node_id = q.node_id
        existing.skill = q.skill
        existing.difficulty = q.difficulty
        return existing

    row = Question(
        id=q.id,
        node_id=q.node_id,
        skill=q.skill,
        type=q.type,
        payload_json=json.dumps(payload, ensure_ascii=False),
        difficulty=q.difficulty,
        verified=bool(q.math_expr),
    )
    db.add(row)
    db.flush()
    return row


def submit_answer(db: DbSession, session: LearningSession, question_id: str, answer: int) -> dict:
    """提交答案，并确保题目属于当前 session 且只能提交一次。"""
    if session.current_question_id != question_id:
        raise ValueError("question is not the current question")

    question = db.get(Question, question_id)
    if question is None:
        raise KeyError(f"question {question_id} not found")

    already_answered = (
        db.query(Attempt)
        .filter(
            Attempt.session_id == session.id,
            Attempt.question_id == question_id,
        )
        .first()
    )
    if already_answered is not None:
        raise ValueError("question has already been answered")

    payload = json.loads(question.payload_json)
    correct, score = score_attempt(payload["correct_index"], answer)
    db.add(Attempt(
        session_id=session.id,
        question_id=question_id,
        answer=answer,
        correct=correct,
        score=score,
    ))

    state = (
        db.query(LearnerState)
        .filter(
            LearnerState.session_id == session.id,
            LearnerState.node_id == question.node_id,
        )
        .first()
    )
    if state is None:
        state = LearnerState(session_id=session.id, node_id=question.node_id)
        db.add(state)

    apply_evidence(state, question.skill, correct)
    state.last_assessed_at = datetime.now(timezone.utc)
    log_event(db, session.id, "answer.submitted", {
        "question_id": question_id,
        "answer": answer,
        "correct": correct,
        "node_id": question.node_id,
        "mastery_after": state.overall,
    })

    if session.stage == SessionStage.DIAGNOSIS.value:
        nxt = next_diagnostic_question(db, session)
        if nxt is None:
            _transition_to_planning(db, session)
            session.current_question_id = None
            db.commit()
            return {"question": None, "stage": session.stage, "correct": correct}
        db.commit()
        return {"question": _question_dict(nxt), "stage": session.stage, "correct": correct}

    if session.stage == SessionStage.ASSESSMENT.value:
        remaining = _remaining_assessment(db, session)
        if not remaining:
            _finish_assessment(db, session)
            session.current_question_id = None
            db.commit()
            return {"question": None, "stage": session.stage, "correct": correct}
        session.current_question_id = remaining[0].id
        db.commit()
        return {"question": _question_dict(remaining[0]), "stage": session.stage, "correct": correct}

    session.current_question_id = None
    db.commit()
    return {"question": None, "stage": session.stage, "correct": correct}


def _transition_to_planning(db: DbSession, session: LearningSession) -> None:
    set_stage(db, session, SessionStage.PLANNING)
    log_event(db, session.id, "diagnosis.completed", {})
    plan = _generate_plan(db, session)
    set_stage(db, session, SessionStage.TEACHING)
    session.current_node_id = plan.current_node
    log_event(db, session.id, "plan.generated", {
        "current_node": plan.current_node,
        "next_nodes": plan.next_nodes,
    })
    db.flush()


def _generate_plan(db: DbSession, session: LearningSession):
    mastery_map = de.get_mastery_map(db, session.id)
    graph = {"nodes": de.get_graph(db), "edges": []}
    plan = PlannerAgent().run(session.goal, mastery_map, graph)
    db.add(Plan(
        session_id=session.id,
        current_node_id=plan.current_node,
        plan_json=json.dumps(plan.model_dump(), ensure_ascii=False),
    ))
    return plan


def tutor_message(db: DbSession, session: LearningSession, content: str) -> dict:
    """生成教学回复并持久化消息。"""
    if session.stage != SessionStage.TEACHING.value:
        raise ValueError("当前不在教学阶段")
    if not content.strip():
        raise ValueError("message cannot be empty")
    if session.current_node_id is None:
        raise ValueError("当前无教学节点")

    node = db.get(KnowledgeNode, session.current_node_id)
    if node is None:
        raise ValueError("当前节点不存在")

    state = (
        db.query(LearnerState)
        .filter(
            LearnerState.session_id == session.id,
            LearnerState.node_id == node.id,
        )
        .first()
    )
    mastery = {
        "overall": state.overall if state else 0.0,
        "conceptual": state.conceptual if state else 0.0,
        "procedural": state.procedural if state else 0.0,
        "transfer": state.transfer if state else 0.0,
    }
    plan = (
        db.query(Plan)
        .filter(Plan.session_id == session.id)
        .order_by(Plan.id.desc())
        .first()
    )
    plan_dict = json.loads(plan.plan_json) if plan else {
        "current_node": node.id,
        "next_nodes": [],
        "rationale": [],
    }

    reply = TutorAgent().run(
        {"id": node.id, "title": node.title, "description": node.description},
        mastery,
        plan_dict,
        content,
    )
    db.add(Message(session_id=session.id, role="user", content=content, node_id=node.id))
    db.add(Message(session_id=session.id, role="tutor", content=reply.content, node_id=node.id))
    log_event(db, session.id, "tutor.replied", {
        "node_id": node.id,
        "intent": reply.intent,
    })
    db.commit()
    return {"content": reply.content, "intent": reply.intent, "node_id": node.id}


def start_assessment(db: DbSession, session: LearningSession) -> Question | None:
    """进入后测并生成 3 道题。"""
    if session.stage != SessionStage.TEACHING.value:
        raise ValueError("只能从教学阶段启动后测")
    if session.current_node_id is None:
        raise ValueError("当前无教学节点")

    node = db.get(KnowledgeNode, session.current_node_id)
    if node is None:
        raise ValueError("当前节点不存在")

    state = (
        db.query(LearnerState)
        .filter(
            LearnerState.session_id == session.id,
            LearnerState.node_id == node.id,
        )
        .first()
    )
    mastery = {"overall": state.overall if state else 0.0}

    set_stage(db, session, SessionStage.ASSESSMENT)
    questions = AssessmentAgent().run(
        {"id": node.id, "title": node.title, "description": node.description},
        mastery,
        node.difficulty,
    )
    rows = [save_question(db, question) for question in questions]
    session.current_question_id = rows[0].id if rows else None
    log_event(db, session.id, "assessment.started", {
        "node_id": node.id,
        "count": len(rows),
    })
    db.commit()
    return rows[0] if rows else None


def _remaining_assessment(db: DbSession, session: LearningSession) -> list[Question]:
    """只返回当前 session 当前节点尚未作答的 assessment 题。"""
    answered_qids = {
        attempt.question_id
        for attempt in db.query(Attempt).filter(Attempt.session_id == session.id).all()
    }
    questions = (
        db.query(Question)
        .filter(
            Question.node_id == session.current_node_id,
            Question.id.like("a_%"),
        )
        .order_by(Question.created_at.asc(), Question.id.asc())
        .all()
    )
    return [question for question in questions if question.id not in answered_qids]


def _finish_assessment(db: DbSession, session: LearningSession) -> None:
    node = db.get(KnowledgeNode, session.current_node_id)
    if node is None:
        raise ValueError("当前节点不存在")

    state = (
        db.query(LearnerState)
        .filter(
            LearnerState.session_id == session.id,
            LearnerState.node_id == node.id,
        )
        .first()
    )
    if state is None:
        raise ValueError("当前节点没有 learner state")

    result = AssessmentResult(
        node_id=node.id,
        conceptual_mastery=state.conceptual,
        procedural_mastery=state.procedural,
        transfer_mastery=state.transfer,
        recommendation="advance" if state.overall >= MASTERY_TARGET else "reteach",
    )
    log_event(db, session.id, "assessment.completed", result.model_dump())

    if state.overall >= MASTERY_TARGET:
        set_stage(db, session, SessionStage.REPLAN)
        _replan(db, session)
    else:
        set_stage(db, session, SessionStage.TEACHING)
        log_event(db, session.id, "assessment.reteach", {"node_id": node.id})
    db.flush()


def _replan(db: DbSession, session: LearningSession) -> None:
    mastery_map = de.get_mastery_map(db, session.id)
    remaining = {
        node_id: mastery
        for node_id, mastery in mastery_map.items()
        if mastery < MASTERY_TARGET
    }
    if not remaining:
        set_stage(db, session, SessionStage.COMPLETE)
        log_event(db, session.id, "learning.completed", {"goal": session.goal})
        return

    plan = _generate_plan(db, session)
    session.current_node_id = plan.current_node
    set_stage(db, session, SessionStage.TEACHING)
    log_event(db, session.id, "replanned", {"current_node": plan.current_node})


def _question_dict(q: Question) -> dict:
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
