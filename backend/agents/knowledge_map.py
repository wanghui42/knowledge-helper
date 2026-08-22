# -*- coding: utf-8 -*-
"""KnowledgeMapAgent：生成主题知识地图。"""
from __future__ import annotations

from agents.providers import LLMProvider, get_provider
from agents.validation import validate_map
from schemas.agent import KnowledgeMap


class KnowledgeMapAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm or get_provider()

    def run(self, subject: str, goal: str) -> KnowledgeMap:
        raw = self.llm.generate_map(subject, goal)
        km = KnowledgeMap.model_validate(raw)
        validate_map(km)  # 节点存在性 + DAG cycle detection → 失败由调用方重新生成
        return km
