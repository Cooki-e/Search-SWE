import subprocess
import unittest
from unittest.mock import patch

from scripts.run_task import prepare_network_probe


class NetworkProbeTests(unittest.TestCase):
    @patch("scripts.run_task.subprocess.run")
    def test_cached_image(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        prepare_network_probe()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[1].args[0][1:3], ["run", "--rm"])

    @patch("scripts.run_task.subprocess.run")
    def test_pull_before_probe(self, run):
        run.side_effect = [subprocess.CompletedProcess([], code, "", "") for code in (1, 0, 0)]
        prepare_network_probe()
        self.assertEqual(run.call_args_list[1].args[0][1], "pull")
        self.assertEqual(run.call_args_list[1].kwargs["timeout"], 300)

    @patch("scripts.run_task.subprocess.run")
    def test_fail_closed(self, run):
        run.side_effect = [subprocess.CompletedProcess([], code, "", "") for code in (0, 1)]
        with self.assertRaisesRegex(RuntimeError, "CONFIG_NFT_FIB_INET"):
            prepare_network_probe()
