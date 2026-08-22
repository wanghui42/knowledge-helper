# -*- coding: utf-8 -*-
"""模型与 Pydantic Schema 共享的枚举常量。"""
from enum import Enum


class SessionStage(str, Enum):
    INIT = "INIT"
    DIAGNOSIS = "DIAGNOSIS"
    PLANNING = "PLANNING"
    TEACHING = "TEACHING"
    ASSESSMENT = "ASSESSMENT"
    REPLAN = "REPLAN"
    COMPLETE = "COMPLETE"


class SkillType(str, Enum):
    CONCEPT = "Concept"
    PROCEDURE = "Procedure"
    TRANSFER = "Transfer"


class RelationType(str, Enum):
    PREREQUISITE = "prerequisite"
    RELATED = "related"


def mastery_level(mastery: float) -> str:
    """按文档第 8 节阈值映射掌握等级。"""
    if mastery < 0.60:
        return "weak"
    if mastery < 0.80:
        return "developing"
    if mastery < 0.90:
        return "mastered"
    return "stable"
