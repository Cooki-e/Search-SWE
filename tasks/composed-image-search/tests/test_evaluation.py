import unittest
from evaluation import ap, composed_map, validate, quality, aggregate


class Tests(unittest.TestCase):
    def test_ideal(self):
        self.assertEqual(composed_map(["a", "b"], {"a": 1, "b": 1}), 1)

    def test_multiple(self):
        self.assertAlmostEqual(
            ap(["x", "a", "b"], {"a": 1, "b": 1}, 5), (1 / 2 + 2 / 3) / 2
        )

    def test_denominator(self):
        self.assertEqual(ap(["a"], {"a": 1, "b": 1, "c": 1}, 2), 0.5)

    def test_empty(self):
        self.assertEqual(composed_map([], {"a": 1}), 0)

    def test_valid(self):
        self.assertEqual(
            validate(
                {"query_id": "q", "reference_image_id": "r"},
                {"query_id": "q", "results": [{"image_id": "a", "score": 1}]},
                {"a": {}},
            ),
            ["a"],
        )

    def test_reference(self):
        with self.assertRaises(ValueError):
            validate(
                {"query_id": "q", "reference_image_id": "r"},
                {"query_id": "q", "results": [{"image_id": "r", "score": 1}]},
                {"r": {}},
            )

    def test_nan(self):
        with self.assertRaises(ValueError):
            validate(
                {"query_id": "q", "reference_image_id": "r"},
                {
                    "query_id": "q",
                    "results": [{"image_id": "a", "score": float("nan")}],
                },
                {"a": {}},
            )


class RelativeProtocolTests(unittest.TestCase):
    def test_recall_cutoffs(self):
        self.assertEqual(quality(["a"], {"a": 1}, "relative"), 1.0)
        self.assertEqual(quality(["x", "a"], {"a": 1}, "relative"), 0.75)
        self.assertEqual(quality(["x"] * 5 + ["a"], {"a": 1}, "relative"), 0.5)
        self.assertEqual(quality([], {"a": 1}, "relative"), 0.0)

    def test_two_sources_have_equal_weight(self):
        rows = [{"domain": "relative", "value": 1.0} for _ in range(6)] + [
            {"domain": "composed", "value": 0.0}
        ]
        self.assertEqual(aggregate(rows)[0], 0.5)
