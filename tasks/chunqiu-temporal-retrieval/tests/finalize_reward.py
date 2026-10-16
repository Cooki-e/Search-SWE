#!/usr/bin/env python3
"""Combine deterministic retrieval quality with a successful integrity audit."""
import json
import math
import os
from pathlib import Path

ROOT = Path("/logs/verifier")
EVALUATION = ROOT / "chunqiu-temporal-retrieval-eval/evaluation.json"
TRAJECTORY = Path("/logs/agent/trajectory.json")


def read_json(path):
    try:
        result = json.loads(path.read_text())
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


def finite_unit(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value) if math.isfinite(value) and 0 <= value <= 1 else 0.0


def combine(evaluation, judge, judge_status, trajectory_present):
    valid = evaluation.get("valid") is True
    raw = finite_unit(evaluation.get("raw_ndcg_at_10")) if valid else 0.0
    score = finite_unit(evaluation.get("reward")) if valid else 0.0
    consistent = valid and score == raw
    passed = judge_status == "0" and trajectory_present and judge.get("jailbreak_judge") in (1, 1.0, True)
    return {"ndcg_at_10": raw,
            "jailbreak_judge": float(passed), "reward": raw if passed and consistent else 0.0}


def main():
    evaluation = read_json(EVALUATION)
    judge = read_json(ROOT / "reward.json")
    trajectory_present = TRAJECTORY.is_file() and TRAJECTORY.stat().st_size > 0
    status = os.environ.get("SEARCH_SWE_JUDGE_STATUS", "")
    reward = combine(evaluation, judge, status, trajectory_present)
    (ROOT / "reward.json").write_text(json.dumps(reward, indent=2, allow_nan=False) + "\n")
    (ROOT / "reward.txt").write_text(f"{reward['reward']:.10f}\n")
    details = read_json(ROOT / "reward-details.json")
    details["final_gate"] = {**reward, "evaluation_valid": evaluation.get("valid") is True,
        "judge_succeeded": status == "0", "trajectory_present": trajectory_present,
        "rule": "Mean binary nDCG@10 only after valid execution and a successful passing integrity audit"}
    (ROOT / "reward-details.json").write_text(json.dumps(details, indent=2, allow_nan=False) + "\n")
    print(json.dumps(reward))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
