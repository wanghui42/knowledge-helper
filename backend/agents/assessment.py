# -*- coding: utf-8 -*-
"""AssessmentAgent：教学后测评。"""
from __future__ import annotations

from agents.providers import LLMProvider, get_provider
from agents.validation import validate_question
from schemas.agent import Question


class AssessmentAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm or get_provider()

    def run(self, node: dict, mastery: dict, difficulty: float) -> list[Question]:
        raws = self.llm.generate_assessment(node, mastery, difficulty)
        questions = [Question.model_validate(r) for r in raws]
        if len(questions) < 3:
            raise ValueError("Assessment 至少需要 3 道题")
        for q in questions:
            validate_question(q)
        return questions
