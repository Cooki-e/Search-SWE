from pathlib import Path
import tomllib
import unittest


class TaskContractTests(unittest.TestCase):
    def test_constraints_do_not_prescribe_a_search_implementation(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "instruction.md", root / "environment/docs/available_resources.md"):
            text = path.read_text().lower()
            self.assertIn("embeddings", text)
            self.assertIn("bm25", text)
            for prescription in ("shell-only", "shell-command", "use bash", "`grep`", "`awk`"):
                self.assertNotIn(prescription, text)
        config = tomllib.loads((root / "task.toml").read_text())
        self.assertNotIn("task_type", config["metadata"])
        self.assertEqual(config["task"]["name"], "search-swe/agentic-search-vectorless")
        self.assertNotIn("shell", config["metadata"]["search_policy"].lower())
        self.assertFalse((root / "environment/starter").exists())


if __name__ == "__main__":
    unittest.main()
