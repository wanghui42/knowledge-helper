# -*- coding: utf-8 -*-
"""diagnostic_engine.py：候选节点选择与停止条件。"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session as DbSession

from models.knowledge import KnowledgeEdge, KnowledgeNode
from models.learner import LearnerState

STOP_MIN_QUESTIONS = 6
MASTERY_HIGH = 0.80
CONSECUTIVE_HIGH_TO_STOP = 3


def get_graph(db: DbSession) -> dict[str, set[str]]:
    """构建 prerequisite 图：target -> 直接 prerequisite source。"""
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.relation == "prerequisite").all()
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge.target_id].add(edge.source_id)
    return dict(graph)


def count_dependents(node_id: str, graph: dict[str, set[str]]) -> int:
    """统计以 node 为 prerequisite 的所有下游节点数量。"""
    visited: set[str] = set()

    def dfs(current: str) -> None:
        for target, sources in graph.items():
            if current in sources and target not in visited:
                visited.add(target)
                dfs(target)

    dfs(node_id)
    return len(visited)


def get_mastery_map(db: DbSession, session_id: str) -> dict[str, float]:
    """只返回有实际答题证据的节点。

    这是区分“未测量”与“掌握度为 0”的关键：LearnerState 可以提前存在，
    但只有 evidence_count > 0 才能进入诊断器的观测状态。
    """
    states = (
        db.query(LearnerState)
        .filter(
            LearnerState.session_id == session_id,
            LearnerState.evidence_count > 0,
        )
        .all()
    )
    return {state.node_id: state.overall for state in states}


def select_next_node(
    db: DbSession,
    nodes: list[KnowledgeNode],
    learner_state: dict[str, float],
    graph: dict[str, set[str]],
) -> KnowledgeNode | None:
    """按 score = uncertainty * importance * (1 + dependency) 选择最高价值节点。

    - 未测节点 mastery = None，uncertainty = 1；
    - 已测节点只要 mastery < 0.80 就仍可进入候选；
    - 已达到 0.80 的节点不再进入诊断候选。
    """
    candidates: list[tuple[float, KnowledgeNode]] = []
    for node in nodes:
        mastery = learner_state.get(node.id)
        if mastery is not None and mastery >= MASTERY_HIGH:
            continue

        uncertainty = 1.0 if mastery is None else max(0.0, 1.0 - mastery)
        dependency = count_dependents(node.id, graph)
        score = uncertainty * node.importance * (1.0 + dependency)
        candidates.append((score, node))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1].difficulty, item[1].id))
    return candidates[0][1]


def should_stop(
    db: DbSession,
    session_id: str,
    learner_state: dict[str, float],
    graph: dict[str, set[str]],
    answered_count: int,
) -> tuple[bool, str]:
    """判断诊断是否应该结束。"""
    if answered_count >= STOP_MIN_QUESTIONS:
        return True, "answered_questions >= 6"

    # 当前实现保持轻量：只在确实已有三个不同节点达到高掌握时提前结束。
    # 由于 get_mastery_map() 只返回有证据节点，不会把默认 0.0 当成已测节点。
    high_nodes = [node_id for node_id, mastery in learner_state.items() if mastery >= MASTERY_HIGH]
    if len(high_nodes) >= CONSECUTIVE_HIGH_TO_STOP:
        return True, "3 high-confidence nodes >= 0.80"

    # 已测 prerequisite 低于阈值时，下游节点暂不继续诊断；
    # 诊断器应优先把证据集中到阻断路径上。
    assessed_nodes = set(learner_state)
    for node_id, prerequisites in graph.items():
        if node_id in assessed_nodes:
            continue
        for prerequisite in prerequisites:
            mastery = learner_state.get(prerequisite)
            if mastery is not None and mastery < MASTERY_HIGH:
                return (
                    True,
                    f"downstream node {node_id} blocked by weak prerequisite {prerequisite}",
                )

    return False, ""
