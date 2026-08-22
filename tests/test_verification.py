# -*- coding: utf-8 -*-
"""SymPy 数学验证单元测试（文档第 17 节：10 个固定数学题全部正确判定）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from services.verification import verify_mcq_derivative, verify_mcq_limit, verify_question

DERIVATIVE_CASES = [
    # (expr, correct_answer, expect)
    ("3*x**2 + 2*x", "6*x + 2", True),
    ("x**3", "3*x**2", True),
    ("x**2", "2*x", True),
    ("(2*x+1)**3", "6*(2*x+1)**2", True),
    ("sin(2*x)", "2*cos(2*x)", True),
    ("exp(x**2)", "2*x*exp(x**2)", True),
    ("x**2", "x", False),  # 错误答案
]

LIMIT_CASES = [
    ("sin(x)/x", "1", "0", True),
    ("x**2 - 1", "3", "2", True),
    ("(1-cos(x))/x**2", "1/2", "0", True),
    ("x**2", "0", "2", False),  # 错误答案
]


def test_derivative_cases():
    for expr, answer, expect in DERIVATIVE_CASES:
        payload = {"math_expr": expr, "correct_answer_expr": answer}
        assert verify_mcq_derivative(payload) == expect, f"case {expr} -> {answer}"


def test_limit_cases():
    for expr, answer, at, expect in LIMIT_CASES:
        payload = {"math_expr": expr, "correct_answer_expr": answer, "limit_at": at}
        assert verify_mcq_limit(payload) == expect, f"case {expr} -> {answer}"


def test_verify_question_dispatch():
    assert verify_question({"verify_type": "derivative", "math_expr": "x**2", "correct_answer_expr": "2*x"}) is True
    assert verify_question({"verify_type": "limit", "math_expr": "x**2", "correct_answer_expr": "4", "limit_at": "2"}) is True
    # 无 math_expr 的纯概念题跳过验证
    assert verify_question({"verify_type": None}) is True


def test_verify_invalid_expr_returns_false():
    assert verify_mcq_derivative({"math_expr": "not_a_valid_expr!!", "correct_answer_expr": "1"}) is False
