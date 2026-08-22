# -*- coding: utf-8 -*-
"""PlannerAgent：选择学习路径。"""
from __future__ import annotations

from agents.providers import LLMProvider, get_provider
from agents.validation import validate_plan
from schemas.agent import Plan


class PlannerAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm or get_provider()

    def run(self, goal: str, learner_states: dict, graph: dict) -> Plan:
        raw = self.llm.generate_plan(goal, learner_states, graph)
        plan = Plan.model_validate(raw)
        validate_plan(plan)
        return plan
