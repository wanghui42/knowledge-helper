# -*- coding: utf-8 -*-
"""diagnostic_engine.py：候选节点选择与停止条件（文档第 9 节）。"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session as DbSession

from models.knowledge import KnowledgeEdge, KnowledgeNode
from models.learner import LearnerState

STOP_MIN_QUESTIONS = 6
MASTERY_HIGH = 0.80
CONSECUTIVE_HIGH_TO_STOP = 3


def get_graph(db: DbSession) -> dict[str, set[str]]:
    """构建 DAG：node_id -> 直接依赖的前驱节点（prerequisite source）。"""
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.relation == "prerequisite").all()
    graph: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        graph[e.target_id].add(e.source_id)
    return dict(graph)


def count_dependents(node_id: str, graph: dict[str, set[str]]) -> int:
    """node 的"下游依赖数"：以 node 为 prerequisite 的节点数（直接或间接）。"""
    visited: set[str] = set()

    def dfs(cur: str) -> None:
        for target, sources in graph.items():
            if cur in sources and target not in visited:
                visited.add(target)
                dfs(target)

    dfs(node_id)
    return len(visited)


def get_mastery_map(db: DbSession, session_id: str) -> dict[str, float]:
    states = db.query(LearnerState).filter(LearnerState.session_id == session_id).all()
    return {s.node_id: s.overall for s in states}


def select_next_node(
    db: DbSession,
    nodes: list[KnowledgeNode],
    learner_state: dict[str, float],
    graph: dict[str, set[str]],
) -> KnowledgeNode | None:
    """按 score = uncertainty * importance * (1 + dependency) 选最高分节点。

    - mastery 未知或 < 0.80 才进入候选；
    - 若候选节点的 prerequisite 全部达标则排除（被阻断）。
    """
    candidates = []
    for node in nodes:
        mastery = learner_state.get(node.id)
        if mastery is not None and mastery >= MASTERY_HIGH:
            continue
        dependency = count_dependents(node.id, graph)
        uncertainty = 1.0 if mastery is None else 1.0 - mastery
        score = uncertainty * node.importance * (1 + dependency)
        candidates.append((score, node))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][1]


def should_stop(
    db: DbSession,
    session_id: str,
    learner_state: dict[str, float],
    graph: dict[str, set[str]],
    answered_count: int,
) -> tuple[bool, str]:
    """诊断停止条件（文档第 9 节）。"""
    if answered_count >= STOP_MIN_QUESTIONS:
        return True, "answered_questions >= 6"

    # 连续 3 个高置信节点 >= 0.80（按诊断顺序，这里近似：当前 >= 0.80 的节点达 3 个）
    high_nodes = [nid for nid, m in learner_state.items() if m >= MASTERY_HIGH]
    if len(high_nodes) >= CONSECUTIVE_HIGH_TO_STOP:
        return True, "3 consecutive high-confidence nodes >= 0.80"

    # 发现下游节点被某个低掌握 prerequisite 阻断
    for node_id, deps in graph.items():
        if node_id in learner_state:
            continue  # 已被诊断过
        for dep in deps:
            if dep in learner_state and learner_state[dep] < MASTERY_HIGH:
                # 存在未达标 prerequisite，阻断下游
                return True, f"downstream node {node_id} blocked by weak prerequisite {dep}"

    return False, ""
