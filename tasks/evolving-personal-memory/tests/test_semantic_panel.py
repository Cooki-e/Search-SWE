import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from semantic_panel import (
    Panel,
    validate_decisions,
    validate_decision_map,
    parse_decision_content,
    judge_input_sha256,
)


class SemanticResponseTests(unittest.TestCase):
    def test_bad_schema_is_not_a_negative_vote(self):
        for value in [
            None,
            [],
            {"decisions": [True]},
            {"decisions": ["YES"]},
            {"decisions": []},
            {"decisions": ["yes"], "extra": 1},
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_decisions(value, 1)

    def test_missing_ids_are_not_silently_shifted(self):
        with self.assertRaises(ValueError):
            validate_decision_map(
                {"decisions": {"c000000": "yes"}}, ["c000000", "c000001"]
            )

    def test_truncation_retries_and_records_both_costs(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(
                "os.environ",
                {
                    "MEMORA_JUDGE_API_KEY": "test-key",
                    "MEMORA_JUDGE_USAGE_PATH": str(Path(d) / "usage.jsonl"),
                },
            ),
        ):
            panel = Panel()
            responses = []
            for content, finish in [
                (None, "length"),
                ('{"decisions":{"c000000":"yes","c000001":"no"}}', "stop"),
            ]:
                r = Mock(status_code=200)
                r.json.return_value = {
                    "id": "response-" + finish,
                    "choices": [
                        {"message": {"content": content}, "finish_reason": finish}
                    ],
                    "usage": {
                        "cost": 0.001,
                        "prompt_tokens": 10,
                        "completion_tokens": 10,
                    },
                }
                responses.append(r)
            with (
                patch("semantic_panel.requests.post", side_effect=responses) as post,
                patch("semantic_panel.time.sleep"),
            ):
                decisions = panel.call(
                    0,
                    {"query_id": "q", "question": "Question"},
                    "Answer",
                    [{"question": "one"}, {"question": "two"}],
                )
            self.assertEqual(decisions, ["yes", "no"])
            self.assertEqual(panel.calls, 2)
            self.assertEqual(panel.retries, 1)
            self.assertEqual(
                post.call_args_list[0].kwargs["json"]["reasoning"], {"enabled": False}
            )
            from semantic_panel import response_format

            schema = response_format(["c000000", "c000001"])["json_schema"]["schema"]
            self.assertEqual(
                schema["properties"]["decisions"]["required"], ["c000000", "c000001"]
            )
            logs = [
                json.loads(x)
                for x in (Path(d) / "usage.jsonl").read_text().splitlines()
            ]
            self.assertEqual(len(logs), 2)
            self.assertFalse(logs[0]["schema_valid"])
            self.assertTrue(logs[1]["schema_valid"])

    def test_persistent_failure_is_infrastructure_error(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(
                "os.environ",
                {
                    "MEMORA_JUDGE_API_KEY": "test-key",
                    "MEMORA_JUDGE_USAGE_PATH": str(Path(d) / "usage.jsonl"),
                },
            ),
        ):
            panel = Panel()
            r = Mock(status_code=200)
            r.json.return_value = {
                "choices": [{"message": {"content": None}, "finish_reason": "length"}]
            }
            with (
                patch("semantic_panel.requests.post", return_value=r),
                patch("semantic_panel.time.sleep"),
                self.assertRaises(RuntimeError),
            ):
                panel.call(
                    1,
                    {"query_id": "q", "question": "Question"},
                    "Answer",
                    [{"question": "one"}],
                )
            self.assertEqual(panel.calls, 3)

    def test_complete_bare_map_and_fenced_json_are_equivalent(self):
        ids = ["c000000", "c000001"]
        bare = '{"c000000":"yes","c000001":"no"}'
        self.assertEqual(parse_decision_content(bare, ids), ["yes", "no"])
        fence = chr(96) * 3
        self.assertEqual(
            parse_decision_content(fence + "json\n" + bare + "\n" + fence, ids),
            ["yes", "no"],
        )

    def test_partial_duplicate_extra_or_ambiguous_output_is_rejected(self):
        ids = ["c000000", "c000001"]
        for content in [
            '{"c000000":"yes"}',
            '{"c000000":"yes","c000001":"no"',
            '{"c000000":"yes","c000001":"no","extra":"yes"}',
            '{"decisions":{"c000000":"yes","c000000":"no","c000001":"no"}}',
            '{"c000000":true,"c000001":"no"}',
        ]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse_decision_content(content, ids)

    def test_cached_votes_are_bound_to_model_answer_and_criteria(self):
        q = {"query_id": "q", "question": "Question"}
        cs = [{"question": "criterion"}]
        d = judge_input_sha256("model", q, "old", cs, 0)
        self.assertNotEqual(d, judge_input_sha256("model", q, "new", cs, 0))
        self.assertNotEqual(d, judge_input_sha256("other", q, "old", cs, 0))
        self.assertNotEqual(
            d, judge_input_sha256("model", q, "old", [{"question": "changed"}], 0)
        )
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                "os.environ",
                {
                    "MEMORA_JUDGE_API_KEY": "test-key",
                    "MEMORA_JUDGE_USAGE_PATH": str(Path(folder) / "usage.jsonl"),
                    "MEMORA_JUDGE_CACHE_PATH": str(Path(folder) / "cache.jsonl"),
                },
            ),
        ):
            from semantic_panel import MODELS

            row = {
                "input_sha256": judge_input_sha256(MODELS[0], q, "old", cs, 0),
                "criteria_start": 0,
                "criteria_count": 1,
                "schema_valid": True,
                "finish_reason": "stop",
                "response_content": '{"decisions":{"c000000":"yes"}}',
            }
            (Path(folder) / "cache.jsonl").write_text(json.dumps(row) + "\n")
            panel = Panel()
            with patch("semantic_panel.requests.post") as post:
                self.assertEqual(panel.call(0, q, "old", cs), ["yes"])
                post.assert_not_called()
            self.assertEqual(panel.cache_hits, 1)

    def test_credit_failure_is_not_retried_or_counted_as_no(self):
        import requests

        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                "os.environ",
                {
                    "MEMORA_JUDGE_API_KEY": "test-key",
                    "MEMORA_JUDGE_USAGE_PATH": str(Path(folder) / "usage.jsonl"),
                },
            ),
        ):
            panel = Panel()
            r = Mock(status_code=402)
            r.raise_for_status.side_effect = requests.HTTPError("insufficient credits")
            with (
                patch("semantic_panel.requests.post", return_value=r) as post,
                patch("semantic_panel.time.sleep"),
                self.assertRaisesRegex(RuntimeError, "HTTP 402"),
            ):
                panel.call(
                    0,
                    {"query_id": "q", "question": "Question"},
                    "Answer",
                    [{"question": "one"}],
                )
            self.assertEqual(post.call_count, 1)

    def test_persistent_partial_json_subdivides_without_guessing_votes(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                "os.environ",
                {
                    "MEMORA_JUDGE_API_KEY": "test-key",
                    "MEMORA_JUDGE_USAGE_PATH": str(Path(folder) / "usage.jsonl"),
                },
            ),
        ):
            panel = Panel()
            responses = []
            contents = ['{"decisions":{"c000000":"yes"'] * 3 + [
                '{"decisions":{"c000000":"yes","c000001":"no","c000002":"yes","c000003":"no"}}',
                '{"decisions":{"c000004":"no","c000005":"yes"}}',
            ]
            for content in contents:
                r = Mock(status_code=200)
                r.json.return_value = {
                    "id": "r" + str(len(responses)),
                    "choices": [
                        {"message": {"content": content}, "finish_reason": "stop"}
                    ],
                    "usage": {"cost": 0.001},
                }
                responses.append(r)
            with (
                patch("semantic_panel.requests.post", side_effect=responses),
                patch("semantic_panel.time.sleep"),
            ):
                result = panel.call(
                    0,
                    {"query_id": "q", "question": "Question"},
                    "Answer",
                    [{"question": "c" + str(i)} for i in range(6)],
                )
            self.assertEqual(result, ["yes", "no", "yes", "no", "no", "yes"])
            logs = [
                json.loads(x)
                for x in (Path(folder) / "usage.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                [x["schema_valid"] for x in logs], [False, False, False, True, True]
            )
            self.assertEqual([x["criteria_start"] for x in logs[-2:]], [0, 4])


if __name__ == "__main__":
    unittest.main()
