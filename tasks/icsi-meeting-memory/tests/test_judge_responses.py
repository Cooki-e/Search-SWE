import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from harness import llm


class JudgeResponseTests(unittest.TestCase):
    def test_missing_final_content_retries_and_keeps_usage(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(
                "os.environ",
                {
                    "ANSWER_JUDGE_API_KEY": "test-key",
                    "ANSWER_JUDGE_BASE_URL": "https://openrouter.ai/api/v1",
                    "ANSWER_JUDGE_MODEL_NAME": "deepseek/deepseek-v4.1-flash",
                    "ICSI_JUDGE_USAGE_PATH": str(Path(d) / "usage.jsonl"),
                },
            ),
        ):
            responses = []
            for content, finish in [(None, "length"), ('{"correct":true}', "stop")]:
                r = Mock(status_code=200)
                r.json.return_value = {
                    "id": "response-" + finish,
                    "choices": [
                        {"message": {"content": content}, "finish_reason": finish}
                    ],
                    "usage": {"cost": 0.001},
                }
                responses.append(r)
            with (
                patch("harness.requests.post", side_effect=responses) as post,
                patch("harness.time.sleep"),
            ):
                value, meta = llm("Return JSON", {"question": "Question"})
            self.assertEqual(value, {"correct": True})
            self.assertEqual(meta["response_id"], "response-stop")
            self.assertEqual(
                post.call_args_list[0].kwargs["json"]["reasoning"], {"enabled": False}
            )
            self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 8192)
            logs = [
                json.loads(x)
                for x in (Path(d) / "usage.jsonl").read_text().splitlines()
            ]
            self.assertEqual(len(logs), 2)
            self.assertFalse(logs[0]["schema_valid"])
            self.assertTrue(logs[1]["schema_valid"])


if __name__ == "__main__":
    unittest.main()
