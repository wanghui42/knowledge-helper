# -*- coding: utf-8 -*-
"""diagnostic engine 单元测试：节点选择与停止条件。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from models.knowledge import KnowledgeEdge, KnowledgeNode
from orchestration import diagnostic_engine as de

# 构造最小图：function -> limit -> derivative
NODES = [
    KnowledgeNode(id="function", subject="math", title="函数", importance=0.9, difficulty=0.3),
    KnowledgeNode(id="limit", subject="math", title="极限", importance=0.9, difficulty=0.5),
    KnowledgeNode(id="derivative", subject="math", title="导数", importance=0.9, difficulty=0.6),
]
EDGES = [
    KnowledgeEdge(id="e1", source_id="function", target_id="limit", relation="prerequisite"),
    KnowledgeEdge(id="e2", source_id="limit", target_id="derivative", relation="prerequisite"),
]


def make_graph():
    import sqlalchemy.orm
    # 直接用内存 dict 模拟 db query 返回
    class FakeDb:
        def query(self, *a, **k):
            return self

        def filter(self, *a, **k):
            return self

        def all(self):
            return EDGES

    return de.get_graph(FakeDb())


def test_select_unknown_first():
    graph = make_graph()
    learner_state: dict[str, float] = {}
    node = de.select_next_node(None, NODES, learner_state, graph)
    # 全部未知时 uncertainty=1.0，score = importance * (1+dependency)
    # function: 0.9*(1+2)=2.7, limit: 0.9*(1+1)=1.8, derivative: 0.9*1=0.9
    assert node.id == "function"


def test_select_skips_mastered():
    graph = make_graph()
    learner_state = {"function": 0.9}
    node = de.select_next_node(None, NODES, learner_state, graph)
    assert node.id == "limit"


def test_select_none_when_all_mastered():
    graph = make_graph()
    learner_state = {"function": 0.9, "limit": 0.9, "derivative": 0.9}
    node = de.select_next_node(None, NODES, learner_state, graph)
    assert node is None


def test_count_dependents():
    graph = make_graph()
    assert de.count_dependents("function", graph) == 2
    assert de.count_dependents("limit", graph) == 1
    assert de.count_dependents("derivative", graph) == 0


def test_should_stop_answered_six():
    graph = make_graph()
    stop, reason = de.should_stop(None, "s", {}, graph, 6)
    assert stop
    assert "answered_questions" in reason


def test_should_stop_not_stopped_early():
    graph = make_graph()
    stop, _ = de.should_stop(None, "s", {}, graph, 3)
    assert not stop


def test_should_stop_high_confidence():
    graph = make_graph()
    learner_state = {"function": 0.85, "limit": 0.9, "derivative": 0.82}
    stop, reason = de.should_stop(None, "s", learner_state, graph, 3)
    assert stop
    assert "high-confidence" in reason
