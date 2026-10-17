"""The compliance gate must accept only a complete binary pass."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("pdf_finalizer", Path(__file__).with_name("finalize_reward.py"))
finalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finalizer)


class FinalizerTests(unittest.TestCase):
    def test_binary_audit_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation = root / "evaluation.json"
            judge = root / "reward.json"
            trajectory = root / "trajectory.json"
            trajectory.write_text("{}")
            evaluation.write_text(json.dumps({"valid": True, "primary_metric": {"value": 0.6}}))
            with patch.multiple(finalizer, REWARD_DIR=root, EVALUATION_PATH=evaluation,
                                JUDGE_REWARD_PATH=judge, DETAILS_PATH=root / "details.json",
                                TRAJECTORY_PATH=trajectory, JUDGE_STATUS="0"):
                for verdict, expected in ((1, 0.6), (True, 0.6), (0, 0),
                                          (0.5, 0), ("1", 0), (2, 0)):
                    with self.subTest(verdict=verdict), patch("builtins.print"):
                        judge.write_text(json.dumps({"jailbreak_judge": verdict}))
                        self.assertEqual(finalizer.main(), 0)
                        self.assertEqual(float((root / "reward.txt").read_text()), expected)


if __name__ == "__main__":
    unittest.main()
