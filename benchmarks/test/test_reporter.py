"""Reporter tests — JSON Lines output + summary."""
import json
import os
import tempfile
import pytest
from benchmarks.core.reporter import JSONLReporter


@pytest.fixture
def tmp_results_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_save_creates_jsonl_file(tmp_results_dir):
    reporter = JSONLReporter(output_dir=tmp_results_dir)
    result = {
        "schema_version": "1.0",
        "run_id": "test-001",
        "task": "face_detection",
        "model": "yunet",
    }
    path = reporter.save(result, task="face_detection")
    assert os.path.exists(path)
    assert path.endswith(".jsonl")


def test_save_appends_to_existing(tmp_results_dir):
    reporter = JSONLReporter(output_dir=tmp_results_dir)
    r1 = {"schema_version": "1.0", "run_id": "001", "task": "face"}
    r2 = {"schema_version": "1.0", "run_id": "002", "task": "face"}
    p1 = reporter.save(r1, task="face")
    p2 = reporter.save(r2, task="face")
    assert p1 == p2
    with open(p1) as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["run_id"] == "001"
    assert json.loads(lines[1])["run_id"] == "002"


def test_each_line_is_valid_json(tmp_results_dir):
    reporter = JSONLReporter(output_dir=tmp_results_dir)
    result = {"schema_version": "1.0", "run_id": "001", "task": "t",
              "nested": {"a": 1, "b": [2, 3]}}
    path = reporter.save(result, task="t")
    with open(path) as f:
        for line in f:
            parsed = json.loads(line)
            assert parsed["nested"]["a"] == 1


def test_build_result_dict():
    reporter = JSONLReporter(output_dir="/tmp")
    result = reporter.build_result(
        task="face_detection",
        model="yunet",
        level=1,
        mode="headless",
        config={"n_warmup": 50, "n_measure": 200},
        latencies_ms=[10.0, 12.0, 11.0, 10.5, 11.5],
        hw_stats={"gpu_util_pct_mean": 0, "ram_mb_peak": 2800,
                  "temp_c_mean": 52, "temp_c_max": 55, "power_w_mean": 8.2},
        ram_baseline_mb=2700,
        crashed=False,
    )
    assert result["schema_version"] == "1.0"
    assert result["task"] == "face_detection"
    assert result["model"] == "yunet"
    assert result["feasibility"]["n_completed"] == 5
    assert result["feasibility"]["fps_mean"] > 0
    assert result["feasibility"]["ram_mb_baseline"] == 2700
    assert result["feasibility"]["ram_mb_delta"] == 100
    assert result["feasibility"]["crashed"] is False
    assert result["quality"] is None
    assert "git_commit" in result
    assert "env_fingerprint" in result
