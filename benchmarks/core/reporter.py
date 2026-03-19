"""Reporter — saves benchmark results as JSON Lines and generates summaries."""
import csv as csv_mod
import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def _get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return "unknown"


def _get_env_fingerprint() -> dict:
    fp = {"python": sys.version.split()[0], "adapter_version": "1.0"}
    try:
        import cv2
        fp["opencv"] = cv2.__version__
    except ImportError:
        pass
    try:
        import onnxruntime
        fp["onnxruntime"] = onnxruntime.__version__
    except ImportError:
        pass
    try:
        import rtmlib
        fp["rtmlib"] = getattr(rtmlib, "__version__", "unknown")
    except ImportError:
        pass
    return fp


class JSONLReporter:
    """Saves each benchmark run as one JSON line in a .jsonl file."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save(self, result: dict, task: str) -> str:
        """Append result to today's JSONL file. Returns file path."""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{task}_{date_str}.jsonl"
        path = os.path.join(self.output_dir, filename)
        with open(path, "a") as f:
            f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
        logger.info(f"Result saved to {path}")
        return path

    def build_result(
        self,
        task: str,
        model: str,
        level: int,
        mode: str,
        config: dict,
        latencies_ms: list[float],
        hw_stats: dict,
        ram_baseline_mb: float,
        crashed: bool,
        quality_metrics: Optional[dict] = None,
        concurrent_models: Optional[list] = None,
        notes: str = "",
    ) -> dict:
        """Build a complete result dict conforming to schema v1.0."""
        n_completed = len(latencies_ms)

        ram_peak = hw_stats.get("ram_mb_peak")
        ram_delta = (ram_peak - ram_baseline_mb) if ram_peak is not None else None

        # Safe FPS/latency calculation
        if n_completed > 0:
            lat = np.array(latencies_ms)
            lat_safe = lat[lat > 0]
            if len(lat_safe) > 0:
                fps_vals = 1000.0 / lat_safe
                fps_mean = round(float(np.mean(fps_vals)), 2)
                fps_median = round(float(np.median(fps_vals)), 2)
                fps_p5 = round(float(np.percentile(fps_vals, 5)), 2)
                fps_std = round(float(np.std(fps_vals)), 2) if len(lat_safe) > 1 else 0.0
            else:
                fps_mean = fps_median = fps_p5 = fps_std = 0.0
            latency_ms_mean = round(float(np.mean(lat)), 2)
            latency_ms_median = round(float(np.median(lat)), 2)
            latency_ms_p99 = round(float(np.percentile(lat, 99)), 2)
        else:
            fps_mean = fps_median = fps_p5 = fps_std = 0.0
            latency_ms_mean = latency_ms_median = latency_ms_p99 = 0.0

        feasibility = {
            "n_completed": n_completed,
            "fps_mean": fps_mean,
            "fps_median": fps_median,
            "fps_p5": fps_p5,
            "fps_std": fps_std,
            "latency_ms_mean": latency_ms_mean,
            "latency_ms_median": latency_ms_median,
            "latency_ms_p99": latency_ms_p99,
            "gpu_util_pct_mean": hw_stats.get("gpu_util_pct_mean"),
            "ram_mb_baseline": ram_baseline_mb,
            "ram_mb_peak": ram_peak,
            "ram_mb_delta": round(ram_delta, 1) if ram_delta is not None else None,
            "temp_c_mean": hw_stats.get("temp_c_mean"),
            "temp_c_max": hw_stats.get("temp_c_max"),
            "power_w_mean": hw_stats.get("power_w_mean"),
            "crashed": crashed,
            "gate_pass": None,
            "task_specific": {},
        }

        quality = None
        if quality_metrics is not None:
            quality = {
                "metrics": quality_metrics,
                "gate_pass": None,
            }

        return {
            "schema_version": "1.0",
            "run_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_commit": _get_git_commit(),
            "env_fingerprint": _get_env_fingerprint(),
            "task": task,
            "model": model,
            "level": level,
            "mode": mode,
            "device": {
                "name": "jetson-orin-nano-8gb",
                "power_mode": "MAXN",
                "concurrent_models": concurrent_models or [],
            },
            "config": config,
            "feasibility": feasibility,
            "quality": quality,
            "decision_hint": None,
            "notes": notes,
        }


class SummaryReporter:
    """Generate comparison summary from multiple JSONL results."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, jsonl_path: str, task: str) -> tuple[str, str]:
        """Read a JSONL file, generate markdown + CSV summaries."""
        results = []
        with open(jsonl_path) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        if not results:
            logger.warning(f"No results in {jsonl_path}")
            return "", ""

        date_str = datetime.now().strftime("%Y%m%d")
        md_path = os.path.join(self.output_dir, f"{task}_{date_str}.md")
        csv_path = os.path.join(self.output_dir, f"{task}_{date_str}.csv")

        self._write_markdown(results, md_path, task)
        self._write_csv(results, csv_path)
        return md_path, csv_path

    def _write_markdown(self, results: list[dict], path: str, task: str):
        lines = [
            f"# {task} Benchmark Summary\n",
            f"> Generated: {datetime.now().isoformat()}\n",
            "",
            "| Model | FPS | Latency (ms) | GPU% | RAM delta (MB) | Power (W) | Gate | Hint |",
            "|-------|:---:|:------------:|:----:|:--------------:|:---------:|:----:|:----:|",
        ]
        for r in results:
            f = r.get("feasibility", {})
            lines.append(
                f"| {r.get('model', '?')} "
                f"| {f.get('fps_mean', '?')} "
                f"| {f.get('latency_ms_mean', '?')} "
                f"| {f.get('gpu_util_pct_mean', '?')} "
                f"| {f.get('ram_mb_delta', '?')} "
                f"| {f.get('power_w_mean', '?')} "
                f"| {'PASS' if f.get('gate_pass') else 'FAIL'} "
                f"| {r.get('decision_hint', '?')} |"
            )
        with open(path, "w") as fout:
            fout.write("\n".join(lines) + "\n")
        logger.info(f"Summary written to {path}")

    def _write_csv(self, results: list[dict], path: str):
        fields = ["model", "fps_mean", "fps_median", "latency_ms_mean",
                   "latency_ms_p99", "gpu_util_pct_mean", "ram_mb_delta",
                   "power_w_mean", "temp_c_max", "crashed", "gate_pass",
                   "decision_hint"]
        with open(path, "w", newline="") as f:
            writer = csv_mod.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in results:
                feas = r.get("feasibility", {})
                row = {
                    "model": r.get("model", ""),
                    "decision_hint": r.get("decision_hint", ""),
                }
                for k in fields:
                    if k not in row:
                        row[k] = feas.get(k, "")
                writer.writerow(row)
        logger.info(f"CSV written to {path}")
