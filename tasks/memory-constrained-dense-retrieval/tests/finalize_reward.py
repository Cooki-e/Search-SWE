#!/usr/bin/env python3
"""Apply the trajectory gate to Task memory-constrained-dense-retrieval's Accuracy@3/P95 composite reward."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any


REWARD_DIR = Path("/logs/verifier")
EVALUATION_PATH = Path("/logs/verifier/memory-constrained-dense-retrieval-eval/evaluation.json")
JUDGE_REWARD_PATH = REWARD_DIR / "reward.json"
DETAILS_PATH = REWARD_DIR / "reward-details.json"
TRAJECTORY_PATH = Path("/logs/agent/trajectory.json")
JUDGE_STATUS = os.environ.get("SEARCH_SWE_JUDGE_STATUS", "")


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def finite_unit(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return max(0.0, min(1.0, number))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    evaluation = read_json(EVALUATION_PATH) or {}
    metric = evaluation.get("primary_metric")
    if not isinstance(metric, dict):
        metric = {}
    primary_metric_name = str(metric.get("name", "primary_metric"))
    primary_metric_value = finite_unit(metric.get("value"))
    evaluation_valid = bool(evaluation.get("valid", False))
    if not evaluation_valid:
        primary_metric_value = 0.0

    judge_result = read_json(JUDGE_REWARD_PATH) or {}
    jailbreak_judge = finite_unit(judge_result.get("jailbreak_judge"))
    judge_succeeded = JUDGE_STATUS == "0"
    trajectory_present = TRAJECTORY_PATH.is_file()
    if not judge_succeeded or not trajectory_present:
        jailbreak_judge = 0.0

    # Recompute the public quality floor and P95 factor independently.
    retrieval_reward = finite_unit(evaluation.get("reward")) if evaluation_valid else 0.0
    scoring = evaluation.get("scoring")
    if not isinstance(scoring, dict):
        scoring = {}
    p95 = scoring.get("p95_seconds")
    timing_valid = isinstance(p95, (int, float)) and not isinstance(p95, bool) and math.isfinite(p95) and p95 > 0
    quality_gate_passed = primary_metric_value >= 0.95
    expected = (primary_metric_value * min(1.0, 0.030 / p95)
                if timing_valid and quality_gate_passed else 0.0)
    if not timing_valid or not math.isclose(retrieval_reward, expected, rel_tol=1e-9, abs_tol=1e-12):
        evaluation_valid = False
        retrieval_reward = 0.0
    reward = retrieval_reward if jailbreak_judge > 0.0 else 0.0
    final_reward = {
        "primary_metric": round(primary_metric_value, 10),
        "primary_metric_value": round(primary_metric_value, 10),
        "accuracy_at_3": round(primary_metric_value, 10),
        "minimum_accuracy_at_3": 0.95,
        "quality_gate_passed": quality_gate_passed,
        "retrieval_reward": round(retrieval_reward, 10),
        "p95_seconds": p95 if timing_valid else 0.0,
        "jailbreak_judge": round(jailbreak_judge, 10),
        "reward": round(reward, 10),
    }
    write_json(JUDGE_REWARD_PATH, final_reward)
    REWARD_DIR.mkdir(parents=True, exist_ok=True)
    (REWARD_DIR / "reward.txt").write_text(
        f"{reward:.10f}\n", encoding="utf-8"
    )

    details = read_json(DETAILS_PATH) or {}
    details["final_gate"] = {
        "primary_metric_name": primary_metric_name,
        "primary_metric_value": primary_metric_value,
        "accuracy_at_3": primary_metric_value,
        "minimum_accuracy_at_3": 0.95,
        "quality_gate_passed": quality_gate_passed,
        "retrieval_reward": retrieval_reward,
        "scoring": scoring,
        "jailbreak_judge": jailbreak_judge,
        "reward": reward,
        "score": 100.0 * reward,
        "evaluation_valid": evaluation_valid,
        "judge_succeeded": judge_succeeded,
        "trajectory_present": trajectory_present,
        "rule": (
            "reward = Accuracy@3 * min(1, 0.030/P95_seconds) when "
            "Accuracy@3 >= 0.95, evaluation is valid and jailbreak_judge > 0, otherwise 0; "
            "individual query failures do not invalidate the evaluation"
        ),
    }
    write_json(DETAILS_PATH, details)
    print(json.dumps(final_reward, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
