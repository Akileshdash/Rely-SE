"""
tests/test_metric_engine.py
============================
Unit tests for MetricEngine. Run with: pytest tests/ -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metric_engine import MetricEngine, ExecutionTrace


def make_trace(**kwargs) -> ExecutionTrace:
    defaults = dict(
        agent="TestAgent", task_id="t-001", trial=1,
        success=True, intervention_required=False,
        commit_proposed=True, build_broken=False,
        regression=False, completed=True,
        duration_seconds=60.0, error_message=""
    )
    defaults.update(kwargs)
    return ExecutionTrace(**defaults)


# ── HIR ──────────────────────────────────────────────────────────────────────

def test_hir_zero():
    traces = [make_trace(intervention_required=False) for _ in range(5)]
    assert MetricEngine().compute_HIR(traces) == 0.0

def test_hir_all():
    traces = [make_trace(intervention_required=True) for _ in range(4)]
    assert MetricEngine().compute_HIR(traces) == 1.0

def test_hir_partial():
    traces = [make_trace(intervention_required=(i < 2)) for i in range(4)]
    assert MetricEngine().compute_HIR(traces) == 0.5

def test_hir_empty():
    assert MetricEngine().compute_HIR([]) == 0.0


# ── CFR ──────────────────────────────────────────────────────────────────────

def test_cfr_no_commits():
    traces = [make_trace(commit_proposed=False) for _ in range(3)]
    assert MetricEngine().compute_CFR(traces) == 0.0

def test_cfr_all_broken():
    traces = [make_trace(commit_proposed=True, build_broken=True) for _ in range(3)]
    assert MetricEngine().compute_CFR(traces) == 1.0

def test_cfr_partial():
    traces = [
        make_trace(commit_proposed=True, build_broken=True),
        make_trace(commit_proposed=True, build_broken=False),
        make_trace(commit_proposed=True, build_broken=False),
        make_trace(commit_proposed=True, build_broken=False),
    ]
    assert MetricEngine().compute_CFR(traces) == 0.25


# ── TSR ──────────────────────────────────────────────────────────────────────

def test_tsr_all_success():
    traces = [make_trace(success=True, regression=False) for _ in range(5)]
    assert MetricEngine().compute_TSR(traces) == 1.0

def test_tsr_regression_counts_as_failure():
    traces = [make_trace(success=True, regression=True)]
    assert MetricEngine().compute_TSR(traces) == 0.0

def test_tsr_mixed():
    traces = [
        make_trace(success=True,  regression=False),
        make_trace(success=True,  regression=False),
        make_trace(success=False, regression=False),
        make_trace(success=True,  regression=True),   # regression → not counted
    ]
    assert MetricEngine().compute_TSR(traces) == 0.5


# ── AGAR ─────────────────────────────────────────────────────────────────────

def test_agar_no_completions():
    traces = [make_trace(completed=False) for _ in range(3)]
    assert MetricEngine().compute_AGAR(traces) == 0.0

def test_agar_all_succeed():
    traces = [make_trace(completed=True, success=True) for _ in range(4)]
    assert MetricEngine().compute_AGAR(traces) == 1.0

def test_agar_partial():
    traces = [
        make_trace(completed=True, success=True),
        make_trace(completed=True, success=True),
        make_trace(completed=True, success=False),
        make_trace(completed=False, success=False),  # not completed → excluded
    ]
    # 2 successes out of 3 completed
    assert abs(MetricEngine().compute_AGAR(traces) - 2/3) < 0.001


# ── DSM ──────────────────────────────────────────────────────────────────────

def test_dsm_all_success():
    assert MetricEngine().compute_DSM([True, True, True]) == 1.0

def test_dsm_all_fail():
    assert MetricEngine().compute_DSM([False, False, False]) == 1.0

def test_dsm_coin_flip():
    # 50/50 → minimum DSM
    assert MetricEngine().compute_DSM([True, False]) == 0.5

def test_dsm_two_thirds():
    result = MetricEngine().compute_DSM([True, True, False])
    assert abs(result - 2/3) < 0.001

def test_dsm_empty():
    assert MetricEngine().compute_DSM([]) == 0.5


# ── compute_all_metrics ───────────────────────────────────────────────────────

def test_compute_all_returns_five_keys():
    engine = MetricEngine()
    traces = [make_trace() for _ in range(3)]
    result = engine.compute_all_metrics(traces)
    assert set(result.keys()) == {"HIR", "CFR", "TSR", "AGAR", "DSM"}

def test_all_metrics_in_range():
    engine = MetricEngine()
    traces = [make_trace(
        success=(i % 2 == 0),
        intervention_required=(i % 3 == 0),
        commit_proposed=True,
        build_broken=(i % 4 == 0),
        regression=False,
        completed=True,
    ) for i in range(9)]
    m = engine.compute_all_metrics(traces)
    assert 0.0 <= m["HIR"]  <= 1.0
    assert 0.0 <= m["CFR"]  <= 1.0
    assert 0.0 <= m["TSR"]  <= 1.0
    assert 0.0 <= m["AGAR"] <= 1.0
    assert 0.5 <= m["DSM"]  <= 1.0
