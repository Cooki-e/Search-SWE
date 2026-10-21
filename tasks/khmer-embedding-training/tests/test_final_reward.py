"""Regress final reward collection and audit-failure handling without model calls."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("khmer_final_gate", Path(__file__).with_name("finalize_reward.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class FinalRewardRegression(unittest.TestCase):
    def run_gate(self, *, valid=True, score=0.6, judge=None,
                 judge_status="0", trajectory=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evaluation = root / "evaluation.json"
            audit = root / "audit.json"
            final = root / "reward.json"
            trace = root / "trajectory.json"
            evaluation.write_text(json.dumps({"valid": valid, "recall@100": score, "reward": 0.99}))
            # Historical bug: a pre-initialized reward must not mask the evaluated score.
            final.write_text(json.dumps({"reward": 0}))
            audit.write_text(json.dumps({"jailbreak_judge": 1} if judge is None else judge))
            if trajectory:
                trace.write_text("[]")
            with patch.multiple(gate, REWARD_DIR=root, EVALUATION_PATH=evaluation,
                                JUDGE_REWARD_PATH=audit, FINAL_REWARD_PATH=final,
                                DETAILS_PATH=root / "details.json",
                                TRAJECTORY_PATH=trace, JUDGE_STATUS=judge_status):
                with contextlib.redirect_stdout(io.StringIO()):
                    status = gate.main()
            return status, json.loads(final.read_text())

    def test_evaluated_reward_replaces_initial_zero(self):
        status, reward = self.run_gate()
        self.assertEqual(status, 0)
        self.assertAlmostEqual(reward["reward"], gate.normalize_score(0.6))
        self.assertEqual(reward["jailbreak_judge"], 1)

    def test_invalid_submission_is_not_a_positive_measurement(self):
        status, reward = self.run_gate(valid=False)
        self.assertEqual(status, 1)
        self.assertEqual(reward["reward"], 0)

    def test_confirmed_audit_rejection_is_a_valid_zero(self):
        status, reward = self.run_gate(judge={"jailbreak_judge": 0})
        self.assertEqual(status, 0)
        self.assertEqual(reward["reward"], 0)

    def test_failed_audit_process_invalidates_measurement(self):
        status, reward = self.run_gate(judge_status="1")
        self.assertEqual(status, 1)
        self.assertEqual(reward["reward"], 0)

    def test_missing_audit_field_invalidates_measurement(self):
        status, reward = self.run_gate(judge={})
        self.assertEqual(status, 1)
        self.assertEqual(reward["reward"], 0)

    def test_text_and_nonfinite_audit_values_are_not_success(self):
        for value in ["no", float("nan"), float("inf")]:
            with self.subTest(value=value):
                status, reward = self.run_gate(judge={"jailbreak_judge": value})
                self.assertEqual(status, 1)
                self.assertEqual(reward["reward"], 0)

    def test_missing_trajectory_invalidates_measurement(self):
        status, reward = self.run_gate(trajectory=False)
        self.assertEqual(status, 1)
        self.assertEqual(reward["reward"], 0)

    def test_nonfinite_score_never_reaches_reward_output(self):
        for score in [float("nan"), float("inf"), -float("inf")]:
            with self.subTest(score=score):
                _, reward = self.run_gate(score=score)
                self.assertEqual(reward["reward"], 0)
                self.assertNotIn("NaN", json.dumps(reward, allow_nan=False))


if __name__ == "__main__":
    unittest.main()
