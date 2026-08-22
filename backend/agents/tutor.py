# -*- coding: utf-8 -*-
"""TutorAgent：当前节点教学。"""
from __future__ import annotations

from agents.providers import LLMProvider, get_provider
from schemas.agent import TutorMessage


class TutorAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm or get_provider()

    def run(self, node: dict, mastery: dict, plan: dict, message: str) -> TutorMessage:
        return TutorMessage.model_validate(
            self.llm.tutor_reply(node, mastery, plan, message)
        )
