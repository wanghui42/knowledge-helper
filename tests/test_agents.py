# -*- coding: utf-8 -*-
"""Agent schema 测试：确定性 provider 输出全部可解析。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from agents.providers import DeterministicProvider
from schemas.agent import KnowledgeMap, Plan, Question

provider = DeterministicProvider()


def test_map_schema_valid():
    raw = provider.generate_map("math", "学习微积分")
    km = KnowledgeMap.model_validate(raw)
    assert len(km.nodes) >= 6
    assert len(km.edges) >= 6


def test_map_acyclic():
    raw = provider.generate_map("math", "学习微积分")
    km = KnowledgeMap.model_validate(raw)
    from agents.validation import assert_acyclic
    assert_acyclic(km)  # 无环


def test_all_questions_parse():
    """题库全部题目可解析为 Question 且选项数=4。"""
    from seed.microcalculus import QUESTION_BANK
    for node_id, questions in QUESTION_BANK.items():
        for q in questions:
            parsed = Question.model_validate(q)
            assert len(parsed.options) == 4
            assert 0 <= parsed.correct_index <= 3


def test_plan_schema_valid():
    raw = provider.generate_plan("学习微积分", {}, {})
    plan = Plan.model_validate(raw)
    assert plan.current_node


def test_tutor_output():
    raw = provider.tutor_reply(
        {"id": "limit", "title": "极限"}, {"overall": 0.3}, {}, "我不太理解"
    )
    assert raw["node_id"] == "limit"
    assert len(raw["content"]) > 50
