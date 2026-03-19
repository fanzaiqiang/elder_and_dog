"""GateEvaluator — check feasibility and quality gates, suggest decision."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GateEvaluator:
    """Stateless evaluator for benchmark gate criteria."""

    @staticmethod
    def check_feasibility(feasibility: dict, gate_config: dict) -> dict:
        """Check feasibility metrics against gate thresholds.
        Uses ram_mb_delta (model increment) for max_ram_mb comparison.
        """
        checks = []
        all_pass = True

        if "min_fps" in gate_config:
            ok = feasibility.get("fps_mean", 0) >= gate_config["min_fps"]
            checks.append({"metric": "fps_mean", "threshold": gate_config["min_fps"],
                           "actual": feasibility.get("fps_mean"), "pass": ok})
            all_pass &= ok

        if "max_ram_mb" in gate_config:
            delta = feasibility.get("ram_mb_delta", 0) or 0
            ok = delta <= gate_config["max_ram_mb"]
            checks.append({"metric": "ram_mb_delta", "threshold": gate_config["max_ram_mb"],
                           "actual": delta, "pass": ok})
            all_pass &= ok

        if "max_power_w" in gate_config:
            power = feasibility.get("power_w_mean") or 0
            ok = power <= gate_config["max_power_w"]
            checks.append({"metric": "power_w_mean", "threshold": gate_config["max_power_w"],
                           "actual": power, "pass": ok})
            all_pass &= ok

        if gate_config.get("must_not_crash", False):
            ok = not feasibility.get("crashed", True)
            checks.append({"metric": "crashed", "threshold": False,
                           "actual": feasibility.get("crashed"), "pass": ok})
            all_pass &= ok

        return {"gate_pass": bool(all_pass), "checks": checks}

    @staticmethod
    def check_quality(quality_metrics: dict, gate_config: dict) -> dict:
        """Check quality metrics against gate thresholds.
        gate_config.metrics keys: min_{name} or max_{name}.
        """
        checks = []
        all_pass = True

        for key, threshold in gate_config.get("metrics", {}).items():
            if key.startswith("min_"):
                metric_name = key[4:]
                actual = quality_metrics.get(metric_name, 0)
                ok = actual >= threshold
            elif key.startswith("max_"):
                metric_name = key[4:]
                actual = quality_metrics.get(metric_name, float("inf"))
                ok = actual <= threshold
            else:
                continue
            checks.append({"metric": metric_name, "threshold": threshold,
                           "actual": actual, "pass": ok})
            all_pass &= ok

        return {"gate_pass": bool(all_pass), "checks": checks}

    @staticmethod
    def suggest_decision(feasibility: dict,
                         quality: Optional[dict] = None) -> str:
        """Suggest a decision code based on gate results. Advisory only."""
        if not feasibility.get("gate_pass", False):
            return "REJECTED"
        if quality is not None and not quality.get("gate_pass", False):
            return "REJECTED"
        gpu = feasibility.get("gpu_util_pct_mean")
        if gpu is not None and gpu > 90:
            return "HYBRID"
        return "JETSON_LOCAL"
