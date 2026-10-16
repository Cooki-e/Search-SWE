"""Author-side tests; no APIs, model inference, or host permission changes."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import grader
import finalize_reward


class OutputContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.jsonl"
        self.queries = [{"query_id": "a", "query": "Find all matching nodes."}]

    def validate(self, rows):
        self.path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return grader.validate_output(self.queries, {0, 1, 2, 3}, output_path=self.path)

    def test_order_is_irrelevant_and_empty_output_set_is_valid(self):
        result = self.validate([{"query_id": "a", "answer_ids": [3, 0, 1]}])
        self.assertTrue(grader.score_answers(result, {"a": {0, 1, 3}})[0]["exact_match"])
        result = self.validate([{"query_id": "a", "answer_ids": []}])
        self.assertTrue(grader.score_answers(result, {"a": set()})[0]["exact_match"])

    def test_missing_extra_and_empty_predictions_have_no_partial_credit(self):
        for ids in ([1], [1, 2, 3], []):
            with self.subTest(ids=ids):
                result = self.validate([{"query_id": "a", "answer_ids": ids}])
                self.assertFalse(grader.score_answers(result, {"a": {1, 2}})[0]["exact_match"])

    def test_invalid_id_types_duplicates_and_unknown_ids(self):
        for ids in ([True], [1.0], ["1"], [None], [1, 1], [999], {}, None):
            with self.subTest(ids=ids), self.assertRaises(grader.VerificationError):
                self.validate([{"query_id": "a", "answer_ids": ids}])

    def test_wrong_duplicate_missing_or_malformed_query_rows(self):
        for rows in ([], [{"query_id": "b", "answer_ids": [1]}],
                     [{"query_id": "a"}], [{"query_id": "a", "answer_ids": [1]}] * 2):
            with self.subTest(rows=rows), self.assertRaises(grader.VerificationError):
                self.validate(rows)
        self.path.write_text("not json\n")
        with self.assertRaises(grader.VerificationError):
            grader.validate_output(self.queries, {1}, output_path=self.path)

    def test_timeout_never_scores_even_for_empty_gold(self):
        rows = [{"query_id": "a", "answer_ids": [], "timed_out": True}]
        self.assertFalse(grader.score_answers(rows, {"a": set()})[0]["exact_match"])


class QueryDeadline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.queries = [{"query_id": x, "query": x} for x in "abc"]
        patches = patch.multiple(grader, OUTPUT_DIR=self.root, RESULTS_DIR=self.root)
        patches.start()
        self.addCleanup(patches.stop)

    def stage(self, rows, *, filename):
        self.assertEqual(len(rows), 1)
        path = self.root / ("input-" + filename)
        path.write_text(json.dumps(rows[0]) + "\n")
        return path

    def success(self, command, **kwargs):
        self.assertEqual(kwargs["timeout"], 30)
        self.assertNotIn("--top-k", command)
        query = json.loads(Path(command[command.index("--queries") + 1]).read_text())
        output = Path(command[command.index("--output") + 1])
        self.assertFalse(output.exists())
        output.write_text(json.dumps({"query_id": query["query_id"], "answer_ids": [1, 2]}) + "\n")
        return {"returncode": 0, "timed_out": False, "elapsed_seconds": .1}

    def test_individual_deadlines_unique_paths_and_timeout_continuation(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            result = self.success(command, **kwargs)
            if len(calls) == 2:
                result.update(returncode=-9, timed_out=True, elapsed_seconds=30.2)
            return result
        metrics = {}
        with patch.object(grader, "stage_queries", side_effect=self.stage), \
             patch.object(grader, "run_timed", side_effect=run):
            rows = grader.run_queries(self.queries, {1, 2}, metrics)
        scored = grader.score_answers(rows, {x: {1, 2} for x in "abc"})
        self.assertEqual([r["exact_match"] for r in scored], [True, False, True])
        self.assertEqual(rows[1]["answer_ids"], [])  # Late correct file is ignored.
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({c[c.index("--output") + 1] for c in calls}), 3)
        self.assertEqual(metrics["per_query_timeout_seconds"], 30)

    def test_non_timeout_exit_and_missing_output_are_contract_failures(self):
        for result in ({"returncode": 7, "timed_out": False, "elapsed_seconds": .1},
                       {"returncode": 0, "timed_out": False, "elapsed_seconds": .1}):
            with self.subTest(result=result), \
                 patch.object(grader, "stage_queries", side_effect=self.stage), \
                 patch.object(grader, "run_timed", return_value=result), \
                 self.assertRaises(grader.VerificationError):
                grader.run_queries(self.queries, {1, 2}, {})

    def test_real_subprocess_timeout(self):
        # Only our own child process group; does not use the submission account.
        with patch.object(grader, "submission_command", side_effect=lambda x: x), \
             patch.object(grader, "SUBMISSION_DIR", self.root):
            result = grader.run_timed(["/bin/sh", "-c", "sleep 10"], timeout=.15,
                                      stdout_path=self.root / "out", stderr_path=self.root / "err")
        self.assertTrue(result["timed_out"])
        self.assertLess(result["elapsed_seconds"], 2)

    def test_fractional_score_includes_timed_out_query(self):
        count = 0
        def run(command, **kwargs):
            nonlocal count
            if command[0].endswith("build.sh"):
                return {"returncode": 0, "timed_out": False, "elapsed_seconds": .1}
            count += 1
            if count == 2:
                return {"returncode": -9, "timed_out": True, "elapsed_seconds": 30.2}
            return self.success(command, **kwargs)
        report = self.root / "evaluation.json"
        with patch.multiple(grader, REPORT_PATH=report, EXECUTION_ERROR=""), \
             patch.object(grader, "recreate_workdirs"), \
             patch.object(grader, "load_corpus", return_value={1, 2}), \
             patch.object(grader, "load_private_data", return_value=(self.queries, {x: {1, 2} for x in "abc"})), \
             patch.object(grader, "check_submission_boundary"), \
             patch.object(grader, "stop_submission_processes"), \
             patch.object(grader, "stage_queries", side_effect=self.stage), \
             patch.object(grader, "run_timed", side_effect=run), patch("builtins.print"):
            grader.main()
        value = json.loads(report.read_text())
        self.assertTrue(value["valid"])
        self.assertEqual(value["reward"], 2 / 3)
        self.assertEqual(value["timed_out_queries"], 1)
        self.assertEqual(value["query_count"], 3)


class IntegrityGate(unittest.TestCase):
    def test_only_submission_credentials_are_forwarded(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "judge-placeholder", "OPENAI_BASE_URL": "judge-host",
                                      "OPENROUTER_API_KEY": "retrieval-placeholder", "JINA_API_KEY": "embedding-placeholder"}):
            command = grader.submission_command(["/app/run.sh"])
        self.assertIn("OPENROUTER_API_KEY=retrieval-placeholder", command)
        self.assertIn("JINA_API_KEY=embedding-placeholder", command)
        self.assertFalse(any(x.startswith(("OPENAI_API_KEY=", "OPENAI_BASE_URL=")) for x in command))

    def test_missing_failing_or_rejecting_judge_cannot_award_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation = root / "evaluation.json"
            evaluation.write_text(json.dumps({"valid": True, "primary_metric": {"value": .65}}))
            reward = root / "reward.json"
            trajectory = root / "trajectory.json"
            trajectory.write_text("{}")
            with patch.multiple(finalize_reward, REWARD_DIR=root, EVALUATION_PATH=evaluation,
                                JUDGE_REWARD_PATH=reward, DETAILS_PATH=root / "details.json", TRAJECTORY_PATH=trajectory), \
                 patch("builtins.print"):
                for status, judgment, expected in [("0", 1, .65), ("0", 0, 0), ("0", .5, 0), ("1", 1, 0), ("", 1, 0)]:
                    reward.write_text(json.dumps({"jailbreak_judge": judgment}))
                    with patch.object(finalize_reward, "JUDGE_STATUS", status):
                        finalize_reward.main()
                    self.assertEqual(json.loads(reward.read_text())["reward"], expected)
                    self.assertEqual(float((root / "reward.txt").read_text()), expected)
                trajectory.unlink()
                reward.write_text('{"jailbreak_judge":1}')
                with patch.object(finalize_reward, "JUDGE_STATUS", "0"):
                    finalize_reward.main()
                self.assertEqual(json.loads(reward.read_text())["reward"], 0)


if __name__ == "__main__":
    unittest.main()
