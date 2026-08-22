# -*- coding: utf-8 -*-
"""Agent 公共验证逻辑（文档第 15 节）。"""
from __future__ import annotations

from schemas.agent import KnowledgeMap, Plan, Question


def validate_question(q: Question) -> None:
    if len(q.options) != 4:
        raise ValueError("Question 必须恰好 4 个选项")
    if not (0 <= q.correct_index <= 3):
        raise ValueError("correct_index 越界")
    if q.math_expr or q.correct_answer_expr:
        from services.verification import verify_question
        if not verify_question(q.model_dump()):
            raise ValueError("SymPy 验证失败：数学题答案不匹配")


def validate_map(km: KnowledgeMap) -> None:
    ids = {n["id"] for n in km.nodes}
    if len(ids) != len(km.nodes):
        raise ValueError("Knowledge Map 节点 id 重复")
    for e in km.edges:
        if e["source"] not in ids or e["target"] not in ids:
            raise ValueError(f"edge 指向不存在的节点: {e}")
        if e["relation"] not in ("prerequisite", "related"):
            raise ValueError(f"非法 relation: {e['relation']}")
    assert_acyclic(km)


def assert_acyclic(km: KnowledgeMap) -> None:
    """DFS 检测环。"""
    adj: dict[str, list[str]] = {n["id"]: [] for n in km.nodes}
    for e in km.edges:
        if e["relation"] == "prerequisite":
            adj[e["source"]].append(e["target"])
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}

    def dfs(u: str) -> bool:
        color[u] = GRAY
        for v in adj[u]:
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    for n in adj:
        if color[n] == WHITE and dfs(n):
            raise ValueError("Knowledge Map 存在环！")


def validate_plan(plan: Plan) -> None:
    if not plan.current_node:
        raise ValueError("Plan 缺少 current_node")
