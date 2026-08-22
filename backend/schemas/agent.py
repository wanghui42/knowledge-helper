# -*- coding: utf-8 -*-
"""Agent 结构化输出 Schema（文档第 14 节）。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Question(BaseModel):
    """DiagnosticAgent / AssessmentAgent 输出。"""
    id: str = Field(description="题目唯一 ID，如 q_xxx")
    node_id: str = Field(description="所属知识节点 ID")
    skill: Literal["Concept", "Procedure", "Transfer"] = Field(description="测评维度")
    type: Literal["mcq"] = "mcq"
    question: str = Field(description="题干（支持 LaTeX）")
    options: list[str] = Field(min_length=4, max_length=4, description="四个选项，第一个为正确项")
    correct_index: int = Field(ge=0, le=3, description="正确选项下标 0-3")
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="难度 0-1")
    # 可验证数学题可选字段
    math_expr: str | None = Field(default=None, description="SymPy 可解析的数学表达式（可选）")
    correct_answer_expr: str | None = Field(default=None, description="SymPy 可解析的正确结果（可选）")
    limit_at: str | None = Field(default=None, description="极限题的自变量趋近值（可选）")
    verify_type: str | None = Field(default=None, description="derivative | limit | None")


class KnowledgeMap(BaseModel):
    """KnowledgeMapAgent 输出。"""
    subject: str
    nodes: list[dict] = Field(description="[{id,title,description,difficulty,importance}]")
    edges: list[dict] = Field(description="[{source,target,relation}] relation=prerequisite|related")
    version: int = 1


class Plan(BaseModel):
    """PlannerAgent 输出。"""
    current_node: str = Field(description="当前应教学节点 ID")
    next_nodes: list[str] = Field(default_factory=list, description="后续节点有序列表")
    rationale: list[str] = Field(default_factory=list, description="选择理由")


class TutorMessage(BaseModel):
    """TutorAgent 输出。"""
    node_id: str = Field(description="教学所属节点")
    content: str = Field(description="Markdown + LaTeX 教学内容")
    intent: Literal["explain", "example", "hint", "question", "feedback"] = "explain"


class AssessmentResult(BaseModel):
    """AssessmentAgent 输出。"""
    node_id: str
    conceptual_mastery: float = Field(ge=0.0, le=1.0)
    procedural_mastery: float = Field(ge=0.0, le=1.0)
    transfer_mastery: float = Field(ge=0.0, le=1.0)
    misconceptions: list[str] = Field(default_factory=list)
    recommendation: str = Field(default="", description="next 动作建议：reteach | advance")


class TutorTurn(BaseModel):
    """教学对话单轮结构（记录用）。"""
    node_id: str
    message: str
