"""JetsonMonitor tests — must work on both dev machine (fallback) and Jetson (jtop).
Note: jtop initialization on Jetson takes ~1s, so sleep times must be generous.
"""
import time
import pytest
from benchmarks.core.monitor import JetsonMonitor


def test_monitor_collects_records():
    """Monitor should collect at least 1 record in 2 seconds on any platform."""
    mon = JetsonMonitor(interval=0.5)
    mon.start()
    time.sleep(2.0)  # jtop needs ~1s init on Jetson
    records = mon.stop()
    assert len(records) >= 1
    for r in records:
        assert "timestamp" in r


def test_monitor_records_have_expected_keys():
    mon = JetsonMonitor(interval=0.5)
    mon.start()
    time.sleep(2.0)
    records = mon.stop()
    assert len(records) >= 1
    expected_keys = {"timestamp", "gpu_util_pct", "cpu_util_pct",
                     "ram_used_mb", "temp_gpu_c", "power_total_mw"}
    for r in records:
        assert expected_keys.issubset(r.keys())


def test_monitor_not_started_returns_empty():
    mon = JetsonMonitor(interval=0.5)
    records = mon.stop()
    assert records == []


def test_monitor_double_stop():
    mon = JetsonMonitor(interval=0.5)
    mon.start()
    time.sleep(2.0)
    r1 = mon.stop()
    r2 = mon.stop()
    assert len(r1) >= 1
    assert r2 == []


def test_aggregate_stats():
    stats = JetsonMonitor.aggregate([
        {"gpu_util_pct": 50, "cpu_util_pct": 30, "ram_used_mb": 2000,
         "temp_gpu_c": 55, "power_total_mw": 8000, "timestamp": 1.0},
        {"gpu_util_pct": 60, "cpu_util_pct": 40, "ram_used_mb": 2200,
         "temp_gpu_c": 58, "power_total_mw": 9000, "timestamp": 1.5},
    ])
    assert stats["gpu_util_pct_mean"] == 55.0
    assert stats["ram_mb_peak"] == 2200
    assert stats["temp_c_max"] == 58
    assert stats["power_w_mean"] == pytest.approx(8.5)
