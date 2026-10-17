from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("run_submission.py")
SPEC = importlib.util.spec_from_file_location("task2_4_runner", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class RunnerTests(unittest.TestCase):
    def test_build_cannot_depend_on_an_agent_phase_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            submission = root / "app"
            submission.mkdir()
            for name in ("build.sh", "run.sh"):
                script = submission / name
                script.write_text("#!/bin/sh\nexit 0\n")
                script.chmod(0o755)
            index = submission / "index"
            index.mkdir()
            marker = index / "agent-index"
            marker.write_text("prebuilt state")
            queries = root / "queries.jsonl"
            queries.write_text('{"query_id":"q","question":"fixture"}\n')
            results = root / "results"
            argv = ["run_submission.py", "--submission-dir", str(submission),
                    "--corpus", str(root / "corpus.jsonl"), "--queries", str(queries),
                    "--qrels", str(root / "qrels"), "--results-dir", str(results),
                    "--evaluator", str(root / "evaluate.py")]

            def build_requiring_prebuilt_index(*args, **kwargs):
                return (0 if marker.exists() else 1), 0.0, None

            with patch.object(RUNNER, "prepare_untrusted_tree"), \
                    patch.object(RUNNER, "prepare_untrusted_runtime"), \
                    patch.object(RUNNER, "run_one", side_effect=build_requiring_prebuilt_index), \
                    patch.object(RUNNER.sys, "argv", argv):
                self.assertEqual(RUNNER.main(), 1)
            self.assertEqual(json.loads((results / "run_manifest.json").read_text())["status"],
                             "build_failed")

    def test_submission_environment_preserves_only_allowed_api_keys(self) -> None:
        values = {
            "API_KEY": "private-secret",
            "MODEL_API": "https://private.invalid/v1",
            "MODEL_NAME": "private-model",
            "OTHER_API_KEY": "other-secret",
            "OPENAI_API_KEY": "agent-secret",
            "OPENAI_BASE_URL": "https://judge.invalid",
            "CODEX_HOME": "/private/judge",
            "HF_TOKEN": "private-download-token",
            "SILICONFLOW_API_KEY": "removed-provider-key",
            "SILICONFLOW_API_BASE_URL": "https://removed-provider.invalid/v1",
            "OPENROUTER_API_KEY": "allowed-openrouter-key",
            "SAFE_VALUE": "kept",
        }
        with patch.dict(os.environ, values, clear=True):
            env = RUNNER.submission_env()
        self.assertNotIn("SAFE_VALUE", env)
        for key in (
            "API_KEY",
            "MODEL_API",
            "MODEL_NAME",
            "OTHER_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "CODEX_HOME",
            "HF_TOKEN",
            "SILICONFLOW_API_KEY",
            "SILICONFLOW_API_BASE_URL",
        ):
            self.assertNotIn(key, env)
        self.assertEqual(env["OPENROUTER_API_KEY"], "allowed-openrouter-key")
        self.assertNotIn("JINA_API_KEY", env)


if __name__ == "__main__":
    unittest.main()
