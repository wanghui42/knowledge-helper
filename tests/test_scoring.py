# -*- coding: utf-8 -*-
"""scoring 单元测试：评分一致性与 mastery 公式。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from models.learner import LearnerState
from services.scoring import apply_evidence, compute_overall, score_attempt, update_mastery


def test_score_attempt_correct():
    correct, score = score_attempt(2, 2)
    assert correct is True
    assert score == 1.0


def test_score_attempt_incorrect():
    correct, score = score_attempt(2, 1)
    assert correct is False
    assert score == 0.0


def test_update_mastery_formula():
    # new = old * 0.65 + evidence * 0.35
    assert update_mastery(0.0, 1.0) == 0.35
    assert update_mastery(1.0, 0.0) == 0.65
    assert update_mastery(0.5, 1.0) == 0.675


def test_compute_overall_weights():
    # 0.5*conceptual + 0.3*procedural + 0.2*transfer
    assert compute_overall(1.0, 0.0, 0.0) == 0.5
    assert compute_overall(0.0, 1.0, 0.0) == 0.3
    assert compute_overall(0.0, 0.0, 1.0) == 0.2
    assert compute_overall(1.0, 1.0, 1.0) == 1.0


def test_apply_evidence_concept():
    state = LearnerState(session_id="s", node_id="n")
    apply_evidence(state, "Concept", True)
    assert state.conceptual == 0.35
    assert state.overall == round(0.5 * 0.35, 4)
    assert state.evidence_count == 1


def test_apply_evidence_procedure():
    state = LearnerState(session_id="s", node_id="n")
    apply_evidence(state, "Procedure", True)
    assert state.procedural == 0.35
    assert state.overall == round(0.3 * 0.35, 4)


def test_apply_evidence_transfer_incorrect():
    state = LearnerState(session_id="s", node_id="n")
    apply_evidence(state, "Transfer", False)
    assert state.transfer == 0.0
    assert state.evidence_count == 1


def test_mastery_threshold_behavior():
    """连续答对可跨越阈值。"""
    state = LearnerState(session_id="s", node_id="n")
    for _ in range(10):
        apply_evidence(state, "Concept", True)
    assert state.conceptual > 0.9
