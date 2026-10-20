import unittest
from evaluation import page_set_f1, validate, aggregate, validate_inputs


class EvidenceTests(unittest.TestCase):
    def test_complete(self):
        self.assertEqual(page_set_f1(["a", "b"], {"a": 1, "b": 1}), 1)

    def test_missing(self):
        self.assertAlmostEqual(page_set_f1(["a"], {"a": 1, "b": 1}), 2 / 3)

    def test_extra(self):
        self.assertAlmostEqual(page_set_f1(["a", "x"], {"a": 1}), 2 / 3)

    def test_no_match(self):
        self.assertEqual(page_set_f1(["x"], {"a": 1}), 0)

    def test_rank_does_not_change_set(self):
        self.assertEqual(page_set_f1(["b", "a"], {"a": 1, "b": 1}), 1)

    def test_wrong_document(self):
        q = {"query_id": "q", "doc_id": "d1", "domain": "visual_reports"}
        pages = {"p": {"domain": "visual_reports", "doc_id": "d2"}}
        with self.assertRaises(ValueError):
            validate(
                q, {"query_id": "q", "results": [{"page_id": "p", "score": 1}]}, pages
            )

    def test_query_mean(self):
        self.assertEqual(
            aggregate(
                [{"domain": "a", "value": 1}] * 3 + [{"domain": "b", "value": 0}]
            )[0],
            0.75,
        )


class InputContract(unittest.TestCase):
    def setUp(self):
        self.q = [
            {
                "query_id": "q",
                "doc_id": "d",
                "domain": "visual_reports",
                "question": "Which figure?",
            }
        ]
        self.pages = {
            "p": {"doc_id": "d", "domain": "visual_reports"},
            "x": {"doc_id": "other", "domain": "visual_reports"},
        }
        self.labels = [{"query_id": "q", "qrels": {"p": 1}}]

    def test_single_actual_domain_is_valid(self):
        self.assertEqual(
            validate_inputs(self.q, self.labels, self.pages), {"q": {"p": 1}}
        )

    def test_wrong_document_gold_is_invalid(self):
        with self.assertRaises(ValueError):
            validate_inputs(self.q, [{"query_id": "q", "qrels": {"x": 1}}], self.pages)

    def test_missing_duplicate_or_empty_inputs(self):
        for qs, ls in [
            (self.q, []),
            (self.q, self.labels * 2),
            (self.q * 2, self.labels),
            ([], self.labels),
        ]:
            with self.subTest(qs=qs, ls=ls), self.assertRaises(ValueError):
                validate_inputs(qs, ls, self.pages)
