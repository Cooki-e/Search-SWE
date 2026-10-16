"""Strict typed-decision validation and deterministic exact accuracy."""
from collections import defaultdict
import json
import math


class VerificationError(ValueError):
    pass


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise VerificationError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise VerificationError(f"Non-finite JSON constant: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)


def validate_answers(answers, questions):
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise VerificationError("Answer keys must match every question exactly")
    for qid, q in questions.items():
        value, kind = answers[qid], q["type"]
        if kind == "choice":
            valid = type(value) is str and value in q["criteria"]
        elif kind == "score":
            valid = type(value) is int and 0 <= value < len(q["criteria"])
        elif kind == "noul":
            valid = type(value) is bool
        else:
            raise VerificationError(f"Unknown question type: {kind}")
        if not valid:
            raise VerificationError(f"Invalid {kind} answer for {qid}")


def score_predictions(requests, references, predictions):
    inputs = {r["request_id"]: r for r in requests}
    gold = {r["request_id"]: r for r in references}
    if not inputs or len(inputs) != len(requests) or len(gold) != len(references) or set(inputs) != set(gold):
        raise VerificationError("Invalid reference coverage")
    seen, counts = set(), defaultdict(lambda: [0, 0])
    for row in predictions:
        if not isinstance(row, dict) or set(row) != {"request_id", "answers"}:
            raise VerificationError("Expected request_id and answers")
        rid = row["request_id"]
        if type(rid) is not str or rid not in inputs or rid in seen:
            raise VerificationError("Unknown, missing or repeated request ID")
        seen.add(rid)
        questions = inputs[rid]["questions"]
        validate_answers(gold[rid]["answers"], questions)
        validate_answers(row["answers"], questions)
        # The frozen suite has exactly one question per request. Retain explicit
        # type checking: Python otherwise treats True as equal to integer 1.
        correct = all(type(row["answers"][q]) is type(gold[rid]["answers"][q])
                      and row["answers"][q] == gold[rid]["answers"][q]
                      for q in questions)
        counts[gold[rid]["dataset"]][0] += int(correct)
        counts[gold[rid]["dataset"]][1] += 1
    if seen != set(inputs):
        raise VerificationError("Incomplete request coverage")
    datasets = {name: {"correct": correct, "count": total, "accuracy": correct / total}
                for name, (correct, total) in sorted(counts.items())}
    accuracy = math.fsum(d["accuracy"] for d in datasets.values()) / len(datasets)
    return {"accuracy": accuracy, "correct": sum(d["correct"] for d in datasets.values()),
            "count": len(inputs), "datasets": datasets}
