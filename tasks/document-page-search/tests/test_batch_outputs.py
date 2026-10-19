"""Regression coverage for recovering independent JSONL query results."""

import json
from pathlib import Path
import tempfile
import unittest

from batch_runtime import completed_rows


class QueryOutputTests(unittest.TestCase):
    def read_rows(self, text):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "results.jsonl"
            path.write_text(text, encoding="utf-8")
            return completed_rows(path)

    def test_bad_json_does_not_discard_surrounding_results(self):
        first, last = {"query_id": "first"}, {"query_id": "last"}
        text = json.dumps(first) + "\nBROKEN\n" + json.dumps(last) + "\n"
        self.assertEqual(self.read_rows(text), [first, last])

    def test_unfinished_final_row_keeps_completed_results(self):
        row = {"query_id": "complete"}
        self.assertEqual(
            self.read_rows(json.dumps(row) + '\n{"query_id":"unfinished"'),
            [row],
        )

    def test_non_object_rows_do_not_discard_valid_results(self):
        row = {"query_id": "valid"}
        self.assertEqual(
            self.read_rows('[]\nnull\n"text"\n' + json.dumps(row) + "\n"),
            [row],
        )

    def test_duplicate_ids_remain_available_for_duplicate_checks(self):
        row = {"query_id": "duplicate"}
        self.assertEqual(
            self.read_rows((json.dumps(row) + "\n") * 2), [row, row]
        )

    def test_missing_output_has_no_completed_results(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(completed_rows(Path(temp) / "missing"), [])

    def test_symlink_is_not_read_as_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "results.jsonl"
            path.write_text('{"query_id":"not-readable-through-link"}\n')
            link = Path(temp) / "link"
            link.symlink_to(path)
            self.assertEqual(completed_rows(link), [])


if __name__ == "__main__":
    unittest.main()
