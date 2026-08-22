# -*- coding: utf-8 -*-
"""DiagnosticAgent：生成诊断题。"""
from __future__ import annotations

from agents.providers import LLMProvider, get_provider
from agents.validation import validate_question
from schemas.agent import Question


class DiagnosticAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm or get_provider()

    def run(self, node: dict, skill: str, difficulty: float) -> Question:
        raw = self.llm.generate_question(node, skill, difficulty)
        q = Question.model_validate(raw)
        validate_question(q)
        return q
