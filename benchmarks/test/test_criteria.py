"""GateEvaluator tests."""
import pytest
from benchmarks.core.criteria import GateEvaluator


def test_feasibility_pass():
    gate_config = {"min_fps": 5.0, "max_ram_mb": 500, "must_not_crash": True}
    feasibility = {
        "fps_mean": 6.6, "ram_mb_delta": 100, "crashed": False,
        "n_completed": 200,
    }
    result = GateEvaluator.check_feasibility(feasibility, gate_config)
    assert result["gate_pass"] is True
    assert len(result["checks"]) == 3


def test_feasibility_fail_fps():
    gate_config = {"min_fps": 10.0, "max_ram_mb": 500, "must_not_crash": True}
    feasibility = {
        "fps_mean": 6.6, "ram_mb_delta": 100, "crashed": False,
        "n_completed": 200,
    }
    result = GateEvaluator.check_feasibility(feasibility, gate_config)
    assert result["gate_pass"] is False


def test_feasibility_fail_crash():
    gate_config = {"min_fps": 1.0, "max_ram_mb": 5000, "must_not_crash": True}
    feasibility = {
        "fps_mean": 6.6, "ram_mb_delta": 100, "crashed": True,
        "n_completed": 50,
    }
    result = GateEvaluator.check_feasibility(feasibility, gate_config)
    assert result["gate_pass"] is False


def test_quality_pass():
    gate_config = {"metrics": {"min_mAP_0.5": 0.70}}
    quality_metrics = {"mAP_0.5": 0.82}
    result = GateEvaluator.check_quality(quality_metrics, gate_config)
    assert result["gate_pass"] is True


def test_quality_fail():
    gate_config = {"metrics": {"min_mAP_0.5": 0.90}}
    quality_metrics = {"mAP_0.5": 0.82}
    result = GateEvaluator.check_quality(quality_metrics, gate_config)
    assert result["gate_pass"] is False


def test_quality_with_max_metric():
    gate_config = {"metrics": {"max_wer": 0.20}}
    quality_metrics = {"wer": 0.15}
    result = GateEvaluator.check_quality(quality_metrics, gate_config)
    assert result["gate_pass"] is True


def test_decision_hint():
    feasibility = {"gate_pass": True, "gpu_util_pct_mean": 95}
    quality = {"gate_pass": True}
    hint = GateEvaluator.suggest_decision(feasibility, quality)
    assert hint in ("JETSON_LOCAL", "CLOUD", "HYBRID", "REJECTED")
