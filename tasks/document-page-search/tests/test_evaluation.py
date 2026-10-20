import unittest, math
from evaluation import ndcg, validate, aggregate


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.q = {"query_id": "q", "domain": "a"}
        self.pages = {"p": {"domain": "a"}, "r": {"domain": "a"}, "x": {"domain": "b"}}

    def prediction(self, rows):
        return {"query_id": "q", "results": rows}

    def test_exact_ideal(self):
        self.assertEqual(ndcg(["p", "r"], {"p": 2, "r": 1}), 1.0)

    def test_linear_gain(self):
        self.assertAlmostEqual(
            ndcg(["r", "p"], {"p": 2, "r": 1}),
            (1 + 2 / math.log2(3)) / (2 + 1 / math.log2(3)),
        )

    def test_missing(self):
        self.assertEqual(ndcg([], {"p": 2}), 0.0)

    def test_valid_empty(self):
        self.assertEqual(validate(self.q, self.prediction([]), self.pages), [])

    def test_duplicates(self):
        with self.assertRaises(ValueError):
            validate(
                self.q,
                self.prediction(
                    [{"page_id": "p", "score": 1}, {"page_id": "p", "score": 1}]
                ),
                self.pages,
            )

    def test_wrong_domain(self):
        with self.assertRaises(ValueError):
            validate(
                self.q, self.prediction([{"page_id": "x", "score": 1}]), self.pages
            )

    def test_bad_scores(self):
        for score in [True, float("nan"), float("inf"), "1"]:
            with self.subTest(score=score), self.assertRaises(ValueError):
                validate(
                    self.q,
                    self.prediction([{"page_id": "p", "score": score}]),
                    self.pages,
                )

    def test_ascending(self):
        with self.assertRaises(ValueError):
            validate(
                self.q,
                self.prediction(
                    [{"page_id": "p", "score": 0}, {"page_id": "r", "score": 1}]
                ),
                self.pages,
            )

    def test_macro(self):
        value, _ = aggregate(
            [{"domain": "a", "value": 1}] * 4 + [{"domain": "b", "value": 0}]
        )
        self.assertEqual(value, 0.5)


if __name__ == "__main__":
    unittest.main()
