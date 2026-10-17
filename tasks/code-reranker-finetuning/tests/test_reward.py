import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("reranker_metric", Path(__file__).with_name("grader.py"))
GRADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GRADER)


class RewardTests(unittest.TestCase):
    def test_attainable_ceiling_receives_full_credit(self):
        self.assertEqual(GRADER.normalized_gain(0.4, 0.8, 0.8), 1)
        self.assertAlmostEqual(GRADER.normalized_gain(0.4, 0.6, 0.8), 0.5)

    def test_no_gain_and_no_headroom_score_zero(self):
        for baseline, submitted, ceiling in ((0.4, 0.4, 0.8), (0.4, 0.2, 0.8),
                                              (0.8, 0.8, 0.8), (0, 0, 0), (1, 1, 1)):
            self.assertEqual(GRADER.normalized_gain(baseline, submitted, ceiling), 0)

    def test_invalid_metrics_rejected(self):
        for metrics in ((0.4, 0.9, 0.8), (0.9, 0.7, 0.8), (-0.1, 0.3, 0.8),
                        (0.1, float("nan"), 0.8), (0.1, 0.2, float("inf"))):
            with self.assertRaises(ValueError):
                GRADER.normalized_gain(*metrics)

    def test_first_stage_misses_remain_in_denominator(self):
        self.assertEqual(GRADER.BRANCH_K, 200)
        ids = [f"d{i}" for i in range(401)]
        corpus = dict.fromkeys(ids, "code")
        candidates = {"hit": ids[:200], "miss": ids[:400]}
        labels = {"hit": {"d0"}, "miss": {"d400"}}
        with patch.object(GRADER, "score_pairs", return_value=list(range(200, 0, -1)) + list(range(400, 0, -1))):
            accuracy, missing = GRADER.accuracy_at_5(None, None, corpus, ["hit", "miss"],
                                                    ["q1", "q2"], labels, candidates, None)
        self.assertEqual(accuracy, 0.5)
        self.assertEqual(missing, 1)
        self.assertEqual(GRADER.normalized_gain(0, accuracy, (2 - missing) / 2), 1)

    def test_candidate_file_requires_exact_branches_and_full_rrf_union(self):
        ids = [f"d{i}" for i in range(501)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in (
                "CORPUS_PATH", "QUERIES_PATH", "GROUND_TRUTH_PATH", "FIRST_STAGE_PATH")}
            paths["CORPUS_PATH"].write_text("".join(
                json.dumps({"_id": doc_id, "text": "code"}) + "\n" for doc_id in ids))
            paths["QUERIES_PATH"].write_text(json.dumps({"_id": "q", "text": "query"}) + "\n")
            paths["GROUND_TRUTH_PATH"].write_text(json.dumps(
                {"query_id": "q", "relevant_doc_ids": ["d499"]}) + "\n")
            with patch.multiple(GRADER, **paths):
                for shift in (0, 100, 200):
                    row = {"qid": "q", "embedding_docids": ids[:200], "bm25_docids": ids[shift:shift + 200]}
                    row["docids"] = GRADER.rrf_fuse(row["embedding_docids"], row["bm25_docids"])
                    paths["FIRST_STAGE_PATH"].write_text(json.dumps(row) + "\n")
                    self.assertEqual(len(row["docids"]), 200 + shift)
                    self.assertEqual(GRADER.load_evaluation_data()[-1], {"q": row["docids"]})
                invalid = [{"qid": "q", "docids": ids[:500]}]  # old single-branch format
                for field in ("embedding_docids", "bm25_docids", "docids"):
                    invalid.extend([{**row, field: row[field][:-1]},
                                    {**row, field: row[field] + ["d499"]},
                                    {**row, field: [row[field][0]] + row[field][:-1]},
                                    {**row, field: ["unknown"] + row[field][1:]},
                                    {**row, field: [None] + row[field][1:]}])
                invalid.append({**row, "docids": list(reversed(row["docids"]))})
                for bad in invalid:
                    with self.subTest(bad=bad):
                        paths["FIRST_STAGE_PATH"].write_text(json.dumps(bad) + "\n")
                        with self.assertRaises(ValueError):
                            GRADER.load_evaluation_data()

    def test_variable_candidate_offsets_are_used_when_scoring(self):
        ids = [f"d{i}" for i in range(400)]
        candidates = {"q1": ids[:200], "q2": ids[:300], "q3": ids}
        labels = {"q1": {"d0"}, "q2": {"d299"}, "q3": {"d399"}}
        scores = [10] + [0] * 199 + [0] * 299 + [10] + [0] * 399 + [10]
        with patch.object(GRADER, "score_pairs", return_value=scores):
            accuracy, missing = GRADER.accuracy_at_5(None, None, dict.fromkeys(ids, "code"),
                list(candidates), ["query"] * 3, labels, candidates, None)
        self.assertEqual((accuracy, missing), (1.0, 0))


if __name__ == "__main__":
    unittest.main()
