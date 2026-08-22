# -*- coding: utf-8 -*-
"""LLM Provider 抽象：真实 OpenAI Agents SDK 与确定性降级实现。"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import config


class AgentError(Exception):
    """Agent 调用失败。"""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """调用 LLM，返回 dict（output_schema 存在时按 schema 结构化）。"""

    def generate_map(self, subject: str, goal: str) -> dict[str, Any]:  # pragma: no cover - 默认抛错
        raise NotImplementedError

    def generate_question(self, node: dict, skill: str, difficulty: float) -> dict[str, Any]:
        raise NotImplementedError

    def generate_plan(self, goal: str, learner_states: dict, graph: dict) -> dict[str, Any]:
        raise NotImplementedError

    def tutor_reply(self, node: dict, mastery: dict, plan: dict, message: str) -> dict[str, Any]:
        raise NotImplementedError

    def generate_assessment(self, node: dict, mastery: dict, difficulty: float) -> list[dict[str, Any]]:
        raise NotImplementedError


def load_prompt(name: str) -> str:
    path = config.BASE_DIR / "prompts" / name
    return path.read_text(encoding="utf-8")


def get_provider() -> LLMProvider:
    """按配置选择 provider：auto = 有 key 走 OpenAI，无 key 走确定性实现。"""
    mode = config.LLM_PROVIDER
    if mode == "deterministic":
        return DeterministicProvider()
    if mode == "openai":
        return OpenAIAgentsProvider()
    if mode == "auto":
        if config.OPENAI_API_KEY:
            return OpenAIAgentsProvider()
        return DeterministicProvider()
    raise ValueError(f"unknown LLM_PROVIDER: {mode}")


class OpenAIAgentsProvider(LLMProvider):
    """基于 OpenAI Agents SDK 的真实实现（结构化输出）。"""

    name = "openai-agents"

    def __init__(self) -> None:
        os.environ.setdefault("OPENAI_API_KEY", config.OPENAI_API_KEY)
        try:
            from agents import Agent, Runner
            from agents.models.openai_responses import OpenAIResponsesModel
        except ImportError as exc:  # pragma: no cover
            raise AgentError("openai-agents 未安装，请 pip install openai-agents") from exc
        self._Runner = Runner
        self._Agent = Agent
        self._model = OpenAIResponsesModel(model_name=config.OPENAI_MODEL)
        self._model_ready = True

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from agents import Agent
        import asyncio

        agent = Agent(
            name="tutor_agent",
            instructions=system_prompt,
            model=self._model,
            output_type=output_schema or dict,
        )
        try:
            result = asyncio.run(self._Runner.run(agent, user_prompt))
            raw = result.final_output
        except Exception as exc:  # pragma: no cover
            raise AgentError(f"OpenAI call failed: {exc}") from exc

        if output_schema is not None:
            # Pydantic 模型 → dict
            if hasattr(raw, "model_dump"):
                return raw.model_dump()
            return json.loads(raw) if isinstance(raw, str) else dict(raw)
        if isinstance(raw, str):
            return {"content": raw}
        return dict(raw)

    # ---- 领域方法统一走 complete + prompt ----
    def generate_map(self, subject: str, goal: str) -> dict[str, Any]:
        from schemas.agent import KnowledgeMap
        user = json.dumps({"subject": subject, "goal": goal}, ensure_ascii=False)
        return self.complete(load_prompt("knowledge_map.md"), user, KnowledgeMap)

    def generate_question(self, node: dict, skill: str, difficulty: float) -> dict[str, Any]:
        from schemas.agent import Question
        user = json.dumps({"node": node, "skill": skill, "difficulty": difficulty}, ensure_ascii=False)
        return self.complete(load_prompt("diagnostic.md"), user, Question)

    def generate_plan(self, goal: str, learner_states: dict, graph: dict) -> dict[str, Any]:
        from schemas.agent import Plan
        user = json.dumps({"goal": goal, "learner_states": learner_states, "graph": graph}, ensure_ascii=False)
        return self.complete(load_prompt("planner.md"), user, Plan)

    def tutor_reply(self, node: dict, mastery: dict, plan: dict, message: str) -> dict[str, Any]:
        from schemas.agent import TutorMessage
        user = json.dumps({"node": node, "mastery": mastery, "plan": plan, "message": message}, ensure_ascii=False)
        return self.complete(load_prompt("tutor.md"), user, TutorMessage)

    def generate_assessment(self, node: dict, mastery: dict, difficulty: float) -> list[dict[str, Any]]:
        from schemas.agent import Question
        user = json.dumps({"node": node, "mastery": mastery, "difficulty": difficulty}, ensure_ascii=False)
        # Assessment 输出为 3 道题的数组
        return [self.complete(load_prompt("assessment.md"), user, Question) for _ in range(3)]


class DeterministicProvider(LLMProvider):
    """无 API Key 时的确定性实现：基于种子题库 / 规则，保证 E2E 闭环可跑。"""

    name = "deterministic"

    def __init__(self) -> None:
        from seed.microcalculus import (
            ASSESSMENT_QUESTIONS,
            KNOWLEDGE_MAP,
            QUESTION_BANK,
            TUTOR_TEMPLATES,
        )
        self.KNOWLEDGE_MAP = KNOWLEDGE_MAP
        self.QUESTION_BANK = QUESTION_BANK
        self.ASSESSMENT_QUESTIONS = ASSESSMENT_QUESTIONS
        self.TUTOR_TEMPLATES = TUTOR_TEMPLATES

    def complete(self, system_prompt: str, user_prompt: str, output_schema=None, **kwargs: Any) -> dict[str, Any]:
        raise AgentError("deterministic provider 不支持通用 complete，请使用领域方法")

    def generate_map(self, subject: str, goal: str) -> dict[str, Any]:
        return self.KNOWLEDGE_MAP

    def generate_question(self, node: dict, skill: str, difficulty: float) -> dict[str, Any]:
        bank = self.QUESTION_BANK.get(node["id"], [])
        # 优先匹配 skill
        for q in bank:
            if q.get("skill") == skill:
                return q
        if bank:
            return bank[0]
        raise AgentError(f"题库中无节点 {node['id']} 的题目")

    def generate_plan(self, goal: str, learner_states: dict, graph: dict) -> dict[str, Any]:
        import orchestration.diagnostic_engine as de
        # 简单规则：选第一个未达标且前置已达标的节点
        nodes = self.KNOWLEDGE_MAP["nodes"]
        node_ids = [n["id"] for n in nodes]
        edges = self.KNOWLEDGE_MAP["edges"]
        deps: dict[str, list[str]] = {}
        for e in edges:
            if e["relation"] == "prerequisite":
                deps.setdefault(e["target"], []).append(e["source"])

        def ready(nid: str) -> bool:
            for p in deps.get(nid, []):
                if learner_states.get(p, 0.0) < 0.80:
                    return False
            return True

        current = None
        next_nodes: list[str] = []
        for nid in node_ids:
            m = learner_states.get(nid, 0.0)
            if m < 0.80 and ready(nid):
                current = nid
                next_nodes = [n for n in node_ids if learner_states.get(n, 0.0) < 0.80 and n != nid]
                break
        if current is None:
            # 全部达标
            current = node_ids[-1] if node_ids else "function"
            next_nodes = []
        return {
            "current_node": current,
            "next_nodes": next_nodes,
            "rationale": [
                f"{current} 尚未掌握（mastery={learner_states.get(current, 0.0):.2f}）且前置已达标",
                "按知识地图依赖顺序优先教学基础节点",
            ],
        }

    def tutor_reply(self, node: dict, mastery: dict, plan: dict, message: str) -> dict[str, Any]:
        # 注意：模板含 LaTeX 花括号，不能使用 str.format；改用占位符替换
        templates = self.TUTOR_TEMPLATES.get(node["id"], self.TUTOR_TEMPLATES["_default"])
        content = (
            templates
            .replace("{title}", node["title"])
            .replace("{mastery}", f"{mastery.get('overall', 0.0):.2f}")
            .replace("{message}", message)
        )
        intent = "feedback" if any(w in message for w in ["不懂", "不会", "再讲", "help", "?"]) else "explain"
        return {"node_id": node["id"], "content": content, "intent": intent}

    def generate_assessment(self, node: dict, mastery: dict, difficulty: float) -> list[dict[str, Any]]:
        bank = self.ASSESSMENT_QUESTIONS.get(node["id"])
        if not bank:
            # 兜底：复用诊断题库前 3 题
            bank = (self.QUESTION_BANK.get(node["id"]) or [])[:3]
        if not bank:
            raise AgentError(f"题库中无节点 {node['id']} 的后测题")
        return list(bank)
