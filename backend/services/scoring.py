# -*- coding: utf-8 -*-
"""scoring.py：单选评分与 mastery 更新（文档第 8 节算法）。"""
from __future__ import annotations

from models.enums import SkillType
from models.learner import LearnerState


def score_attempt(correct_index: int, answer: int) -> tuple[bool, float]:
    """程序比对 correct_index，正确得 1.0，错误得 0.0。"""
    correct = answer == correct_index
    return correct, 1.0 if correct else 0.0


def _norm(v: float | None) -> float:
    """把 None（SQLAlchemy 未 flush 的 default）视为 0.0。"""
    return 0.0 if v is None else float(v)


def update_mastery(old: float | None, evidence: float, decay: float = 0.35) -> float:
    """new = old * (1 - decay) + evidence * decay"""
    return round(_norm(old) * (1 - decay) + evidence * decay, 4)


def apply_evidence(state: LearnerState, skill: str | SkillType, correct: bool) -> LearnerState:
    """把单题证据更新到对应 skill 维度，并重算 overall。"""
    evidence = 1.0 if correct else 0.0
    decay = 0.35

    if skill == SkillType.PROCEDURE or skill == "Procedure" or skill == "procedure":
        state.procedural = update_mastery(state.procedural, evidence, decay)
    elif skill == SkillType.TRANSFER or skill == "Transfer" or skill == "transfer":
        state.transfer = update_mastery(state.transfer, evidence, decay)
    else:  # Concept / 默认
        state.conceptual = update_mastery(state.conceptual, evidence, decay)

    state.evidence_count = (state.evidence_count or 0) + 1
    state.overall = compute_overall(state.conceptual, state.procedural, state.transfer)
    return state


def compute_overall(conceptual: float | None, procedural: float | None, transfer: float | None) -> float:
    """mastery = 0.5*conceptual + 0.3*procedural + 0.2*transfer"""
    return round(0.5 * _norm(conceptual) + 0.3 * _norm(procedural) + 0.2 * _norm(transfer), 4)
