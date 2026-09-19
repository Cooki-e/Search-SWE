import json
import unittest
from unittest.mock import AsyncMock, patch

from harbor.models.trajectories.trajectory import Trajectory
from scripts.harbor_agents import PreinstalledPi, Pi
from scripts.pi_trajectory import convert_events


def stream(*messages):
    return "\n".join(json.dumps({"type": "message_end", "message": m}) for m in messages)


class PiTrajectoryTests(unittest.TestCase):
    def test_tools_and_schema(self):
        text = stream(
            {"role": "assistant", "content": [{"type": "toolCall", "id": "a", "name": "bash", "arguments": {"command": "ls"}}], "stopReason": "toolUse"},
            {"role": "toolResult", "toolCallId": "a", "content": [{"type": "text", "text": "file"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "done"}], "stopReason": "stop"},
        )
        trajectory, error = convert_events(text, "task", "model", "version")
        Trajectory.model_validate(trajectory)
        self.assertIsNone(error)
        self.assertEqual(len(trajectory["steps"]), 3)
        self.assertIn("file", trajectory["steps"][1]["observation"]["results"][0]["content"])

    def test_terminal_error(self):
        _, error = convert_events(stream({"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "Request timed out."}), "task", "m", "v")
        self.assertEqual(error, "Request timed out.")

    def test_recovered_error(self):
        _, error = convert_events(stream(
            {"role": "assistant", "content": [], "stopReason": "error"},
            {"role": "assistant", "content": [], "stopReason": "stop"},
        ), "task", "m", "v")
        self.assertIsNone(error)

    def test_empty_output_fails(self):
        self.assertIsNotNone(convert_events("diagnostic", "task", "m", "v")[1])


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_exports_before_raising(self):
        agent = object.__new__(PreinstalledPi)
        agent.model_name = "deepseek/deepseek-flash"
        agent._upload_config_text = AsyncMock()
        environment = AsyncMock()

        async def download(remote, local):
            local.write_text(stream({"role": "assistant", "content": [], "stopReason": "error", "errorMessage": "timeout"}))

        environment.download_file.side_effect = download
        with patch.object(Pi, "run", new_callable=AsyncMock):
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                await agent.run("task", environment, None)
        uploaded = agent._upload_config_text.call_args.kwargs
        self.assertEqual(uploaded["remote_path"], "/logs/agent/trajectory.json")
        Trajectory.model_validate_json(uploaded["content"])


if __name__ == "__main__":
    unittest.main()
