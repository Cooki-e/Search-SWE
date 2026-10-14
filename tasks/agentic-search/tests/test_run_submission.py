from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("run_submission.py")
SPEC = importlib.util.spec_from_file_location("agentic_search_runner", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class RunnerTests(unittest.TestCase):
    def test_submission_environment_preserves_only_allowed_api_keys(self) -> None:
        values = {
            "API_KEY": "private-secret",
            "MODEL_API": "https://private.invalid/v1",
            "MODEL_NAME": "private-model",
            "OTHER_API_KEY": "other-secret",
            "OPENAI_API_KEY": "agent-secret",
            "OPENAI_BASE_URL": "https://judge.invalid/v1",
            "VERIFIER_OPENAI_API_KEY": "judge-secret",
            "VERIFIER_OPENAI_BASE_URL": "https://judge.invalid/v1",
            "AGENT_OPENAI_API_KEY": "coding-agent-secret",
            "ANSWER_JUDGE_API_KEY": "answer-judge-secret",
            "SILICONFLOW_API_KEY": "removed-provider-key",
            "SILICONFLOW_API_BASE_URL": "https://removed-provider.invalid/v1",
            "OPENROUTER_API_KEY": "allowed-openrouter-key",
            "JINA_API_KEY": "allowed-jina-key",
            "PYTHONUNBUFFERED": "1",
            "UNDECLARED_VALUE": "removed",
            "REACT_MODEL": "qwen/qwen3.5-9b",
        }
        with patch.dict(os.environ, values, clear=True):
            env = RUNNER.submission_env()
        self.assertEqual(env["PYTHONUNBUFFERED"], "1")
        self.assertEqual(env["REACT_MODEL"], "qwen/qwen3.5-9b")
        for key in (
            "API_KEY",
            "MODEL_API",
            "MODEL_NAME",
            "OTHER_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "VERIFIER_OPENAI_API_KEY",
            "VERIFIER_OPENAI_BASE_URL",
            "AGENT_OPENAI_API_KEY",
            "ANSWER_JUDGE_API_KEY",
            "UNDECLARED_VALUE",
            "SILICONFLOW_API_KEY",
            "SILICONFLOW_API_BASE_URL",
        ):
            self.assertNotIn(key, env)
        self.assertEqual(env["OPENROUTER_API_KEY"], "allowed-openrouter-key")
        self.assertEqual(env["JINA_API_KEY"], "allowed-jina-key")


if __name__ == "__main__":
    unittest.main()
