"""Pure contract checks; these tests do not launch submission processes."""
import copy
import json
import unittest

from scoring import VerificationError, strict_json, score_predictions, validate_answers


class DecisionScoring(unittest.TestCase):
    def setUp(self):
        self.requests = [
            {"request_id": "a", "questions": {"q": {"type": "choice", "criteria": {"A": "", "B": ""}}}},
            {"request_id": "b", "questions": {"q": {"type": "noul"}}},
            {"request_id": "c", "questions": {"q": {"type": "score", "criteria": ["low", "mid", "high"]}}},
        ]
        self.gold = [{"request_id": "a", "dataset": "first", "answers": {"q": "B"}},
                     {"request_id": "b", "dataset": "first", "answers": {"q": True}},
                     {"request_id": "c", "dataset": "second", "answers": {"q": 1}}]
        self.correct = [{"request_id": r["request_id"], "answers": copy.deepcopy(r["answers"])} for r in self.gold]

    def test_correct_and_output_reordering(self):
        self.assertEqual(score_predictions(self.requests, self.gold, self.correct[::-1])["accuracy"], 1.0)

    def test_macro_accuracy_arithmetic(self):
        rows = copy.deepcopy(self.correct)
        rows[0]["answers"]["q"] = "A"
        result = score_predictions(self.requests, self.gold, rows)
        self.assertEqual(result["correct"], 2)
        self.assertEqual(result["datasets"]["first"]["accuracy"], 0.5)
        self.assertEqual(result["accuracy"], 0.75)

    def test_all_wrong(self):
        rows = copy.deepcopy(self.correct)
        for row, value in zip(rows, ("A", False, 0)):
            row["answers"]["q"] = value
        self.assertEqual(score_predictions(self.requests, self.gold, rows)["accuracy"], 0.0)

    def test_typed_labels(self):
        for position, values in [(0, [0, True, "C"]), (1, [1, "true", None]), (2, [True, 1.0, "1", -1, 3])]:
            for value in values:
                with self.subTest(position=position, value=value), self.assertRaises(VerificationError):
                    validate_answers({"q": value}, self.requests[position]["questions"])

    def test_coverage(self):
        for rows in ([], self.correct[:2], self.correct + self.correct[:1]):
            with self.assertRaises(VerificationError):
                score_predictions(self.requests, self.gold, rows)
        bad = copy.deepcopy(self.correct)
        bad[0]["request_id"] = "unknown"
        with self.assertRaises(VerificationError):
            score_predictions(self.requests, self.gold, bad)

    def test_answer_keys(self):
        for value in ({}, {"other": "A"}, {"q": "A", "extra": "B"}, [], None):
            with self.assertRaises(VerificationError):
                validate_answers(value, self.requests[0]["questions"])

    def test_json_ambiguities(self):
        for text in ('{"q":1,"q":2}', '{"q":NaN}', '{"q":Infinity}', '{"q":-Infinity}', '{bad'):
            with self.assertRaises((VerificationError, json.JSONDecodeError)):
                strict_json(text)

    def test_missing_reference(self):
        with self.assertRaises(VerificationError):
            score_predictions(self.requests, self.gold[:2], self.correct)


if __name__ == "__main__":
    unittest.main()
