# -*- coding: utf-8 -*-
"""LLM Provider 抽象：OpenAI Agents SDK + deterministic fallback。"""
from __future__ import annotations

import asyncio
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
        """同步接口，返回结构化 dict。"""

    def generate_map(self, subject: str, goal: str) -> dict[str, Any]:
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
    return (config.BASE_DIR / "prompts" / name).read_text(encoding="utf-8")


def get_provider() -> LLMProvider:
    mode = config.LLM_PROVIDER
    if mode == "deterministic":
        return DeterministicProvider()
    if mode == "openai":
        return OpenAIAgentsProvider()
    if mode == "auto":
        return OpenAIAgentsProvider() if config.OPENAI_API_KEY else DeterministicProvider()
    raise ValueError(f"unknown LLM_PROVIDER: {mode}")


class OpenAIAgentsProvider(LLMProvider):
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

    async def complete_async(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        agent = self._Agent(
            name="tutor_agent",
            instructions=system_prompt,
            model=self._model,
            output_type=output_schema or dict,
        )
        try:
            result = await self._Runner.run(agent, user_prompt)
            raw = result.final_output
        except Exception as exc:  # pragma: no cover
            raise AgentError(f"OpenAI call failed: {exc}") from exc

        if output_schema is not None:
            if hasattr(raw, "model_dump"):
                return raw.model_dump()
            return json.loads(raw) if isinstance(raw, str) else dict(raw)
        if isinstance(raw, str):
            return {"content": raw}
        return dict(raw)

    def complete(self, system_prompt: str, user_prompt: str, output_schema: type | None = None, **kwargs: Any) -> dict[str, Any]:
        """同步兼容层。

        Web async endpoint 不应直接调用此方法；它会在线程池中执行。
        这样可以避免在已有 event loop 的线程中调用 asyncio.run()。
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.complete_async(system_prompt, user_prompt, output_schema, **kwargs))
        raise AgentError("complete() cannot run inside an active event loop; use complete_async()")

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
        return [self.complete(load_prompt("assessment.md"), user, Question) for _ in range(3)]


class DeterministicProvider(LLMProvider):
    name = "deterministic"

    def __init__(self) -> None:
        from seed.microcalculus import ASSESSMENT_QUESTIONS, KNOWLEDGE_MAP, QUESTION_BANK, TUTOR_TEMPLATES
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
        for question in bank:
            if question.get("skill") == skill:
                return question
        if bank:
            return bank[0]
        raise AgentError(f"题库中无节点 {node['id']} 的题目")

    def generate_plan(self, goal: str, learner_states: dict, graph: dict) -> dict[str, Any]:
        nodes = self.KNOWLEDGE_MAP["nodes"]
        node_ids = [node["id"] for node in nodes]
        edges = self.KNOWLEDGE_MAP["edges"]
        deps: dict[str, list[str]] = {}
        for edge in edges:
            if edge["relation"] == "prerequisite":
                deps.setdefault(edge["target"], []).append(edge["source"])

        def ready(node_id: str) -> bool:
            return all(learner_states.get(dep, 0.0) >= 0.80 for dep in deps.get(node_id, []))

        current = next((node_id for node_id in node_ids if learner_states.get(node_id, 0.0) < 0.80 and ready(node_id)), None)
        if current is None:
            current = node_ids[-1] if node_ids else "function"
            next_nodes: list[str] = []
        else:
            next_nodes = [node_id for node_id in node_ids if learner_states.get(node_id, 0.0) < 0.80 and node_id != current]

        return {
            "current_node": current,
            "next_nodes": next_nodes,
            "rationale": [
                f"{current} 尚未掌握（mastery={learner_states.get(current, 0.0):.2f}）且前置已达标",
                "按知识地图依赖顺序优先教学基础节点",
            ],
        }

    def tutor_reply(self, node: dict, mastery: dict, plan: dict, message: str) -> dict[str, Any]:
        templates = self.TUTOR_TEMPLATES.get(node["id"], self.TUTOR_TEMPLATES["_default"])
        content = (
            templates
            .replace("{title}", node["title"])
            .replace("{mastery}", f"{mastery.get('overall', 0.0):.2f}")
            .replace("{message}", message)
        )
        intent = "feedback" if any(word in message for word in ["不懂", "不会", "再讲", "help", "?"]) else "explain"
        return {"node_id": node["id"], "content": content, "intent": intent}

    def generate_assessment(self, node: dict, mastery: dict, difficulty: float) -> list[dict[str, Any]]:
        bank = self.ASSESSMENT_QUESTIONS.get(node["id"])
        if not bank:
            bank = (self.QUESTION_BANK.get(node["id"]) or [])[:3]
        if not bank:
            raise AgentError(f"题库中无节点 {node['id']} 的后测题")
        return list(bank)
