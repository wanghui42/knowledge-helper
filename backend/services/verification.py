# -*- coding: utf-8 -*-
"""verification.py：SymPy 数学验证服务（文档第 15 节）。"""
from __future__ import annotations

import sympy as sp


def verify_mcq_derivative(payload: dict) -> bool:
    """验证求导类选择题：用 SymPy 重算导数，检查正确选项是否与解析结果等价。

    支持 payload 内 "math_expr"（被求导表达式）与 "correct_answer_expr"。
    若题目不含 math_expr 字段则无法验证，返回 True（跳过）。
    """
    expr_str = payload.get("math_expr")
    correct_str = payload.get("correct_answer_expr")
    if not expr_str or not correct_str:
        return True  # 非可验证题型，跳过
    try:
        x = sp.symbols("x")
        expr = sp.sympify(expr_str)
        derivative = sp.diff(expr, x)
        expected = sp.sympify(correct_str)
        return sp.simplify(derivative - expected) == 0
    except Exception:
        return False


def verify_mcq_limit(payload: dict) -> bool:
    """验证极限类选择题：SymPy 重算极限。"""
    expr_str = payload.get("math_expr")
    correct_str = payload.get("correct_answer_expr")
    at_str = payload.get("limit_at", "0")
    if not expr_str or not correct_str:
        return True
    try:
        x = sp.symbols("x")
        expr = sp.sympify(expr_str)
        at = sp.sympify(at_str)
        limit = sp.limit(expr, x, at)
        expected = sp.sympify(correct_str)
        return sp.simplify(limit - expected) == 0
    except Exception:
        return False


def verify_question(payload: dict) -> bool:
    """按题目类型分派验证；无法验证的返回 True。"""
    qtype = (payload.get("verify_type") or "").lower()
    if qtype in ("derivative", "differentiation"):
        return verify_mcq_derivative(payload)
    if qtype == "limit":
        return verify_mcq_limit(payload)
    return True
