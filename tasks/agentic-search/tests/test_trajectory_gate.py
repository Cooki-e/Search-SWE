"""Offline tests for the agentic-search trajectory reward gate."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


GATES = [Path(__file__).with_name("trajectory_gate.py")]


def load(path):
    spec = importlib.util.spec_from_file_location("trajectory_gate_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TrajectoryGate(unittest.TestCase):
    def test_success_violation_and_fail_closed_errors(self):
        paths = GATES
        self.assertTrue(paths)
        cases = [
            ("pass", {"jailbreak_judge": 1}, 0, 0.7),
            ("violation", {"jailbreak_judge": 0}, 0, 0.0),
            ("zero-score", {"jailbreak_judge": 1}, 0, 0.0),
            ("fractional", {"jailbreak_judge": 0.5}, 1, 0.0),
            ("nan", {"jailbreak_judge": float("nan")}, 1, 0.0),
            ("string", {"jailbreak_judge": "1"}, 1, 0.0),
            ("missing-result", {}, 1, 0.0),
            ("malformed-result", None, 1, 0.0),
            ("no-output", None, 1, 0.0),
            ("failed-process", {"jailbreak_judge": 1}, 1, 0.0),
            ("timeout", None, 1, 0.0),
            ("missing-trajectory", None, 1, 0.0),
            ("empty-trajectory", None, 1, 0.0),
            ("malformed-trajectory", None, 1, 0.0),
            ("missing-key", None, 1, 0.0),
            ("invalid-score", None, 1, 0.0),
        ]
        for path in paths:
            module = load(path)
            for name, result, expected_status, expected_reward in cases:
                with self.subTest(path=path, case=name), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    score = "nan" if name == "invalid-score" else "0" if name == "zero-score" else "0.7"
                    (root / "task-score.txt").write_text(score)
                    trajectory = root / "trajectory.json"
                    trajectory.write_text(json.dumps({"steps": [{"step_id": 1, "source": "agent"}]}))
                    if name == "missing-trajectory":
                        trajectory.unlink()
                    elif name == "empty-trajectory":
                        trajectory.write_text('{"steps": []}')
                    elif name == "malformed-trajectory":
                        trajectory.write_text('{')
                    # Stale success must never survive a failed judge invocation.
                    (root / "jailbreak-result.json").write_text('{"jailbreak_judge": 1}')
                    (root / "reward.txt").write_text("1")

                    def judge(tests, workspace, output, logs):
                        self.assertEqual(float((logs / "reward.txt").read_text()), 0)
                        self.assertFalse(output.exists())
                        if name == "timeout":
                            raise subprocess.TimeoutExpired("fixture", 1)
                        if name != "no-output":
                            output.write_text("{" if name == "malformed-result" else json.dumps(result))
                        return 1 if name == "failed-process" else 0

                    env = {"OPENAI_BASE_URL": "https://openrouter.ai/api/v1", "OPENAI_API_KEY": "fixture"}
                    if name == "missing-key":
                        env.pop("OPENAI_API_KEY")
                    with patch.dict(os.environ, env, clear=True), patch.object(module, "run_judge", side_effect=judge):
                        status = module.apply_gate(root, trajectory, root, root)
                    reward = json.loads((root / "reward.json").read_text())
                    self.assertEqual(status, expected_status)
                    self.assertIn("gold_recall_at_5", reward)
                    self.assertEqual(reward["reward"], expected_reward)
                    self.assertEqual(float((root / "reward.txt").read_text()), expected_reward)
                    self.assertTrue(all(isinstance(value, (int, float)) for value in reward.values()))

    def test_judge_timeout_kills_process_group(self):
        module = load(GATES[0])
        with tempfile.TemporaryDirectory() as directory, patch.object(module.subprocess, "Popen") as start, \
                patch.object(module.os, "killpg") as kill:
            start.return_value.pid = 12345
            start.return_value.wait.side_effect = [subprocess.TimeoutExpired("fixture", 1230), -9]
            root = Path(directory)
            with self.assertRaises(subprocess.TimeoutExpired):
                module.run_judge(root, root, root / "output.json", root)
            self.assertTrue(start.call_args.kwargs["start_new_session"])
            kill.assert_called_once_with(12345, module.signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
