"""Sketch and text ranking contract and Recall/MRR quality."""

import math, json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def quality(ids, qrels, k=3):
    relevant = {key for key, value in qrels.items() if value > 0}
    hit = next((i + 1 for i, key in enumerate(ids[:k]) if key in relevant), None)
    return 0.5 * (1 + 1 / hit) if hit else 0.0


def validate(q, p, pages):
    if not isinstance(p, dict) or p.get("query_id") != q["query_id"]:
        raise ValueError("Query ID mismatch")
    rows = p.get("results")
    if not isinstance(rows, list) or len(rows) > 10:
        raise ValueError("Expected at most ten results")
    ids = []
    last = math.inf
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid result")
        pid = row.get("image_id")
        score = row.get("score")
        if not isinstance(pid, str) or pid not in pages or pid in ids:
            raise ValueError("Invalid, duplicate or wrong-domain page")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
            or score > last
        ):
            raise ValueError("Invalid ranking score")
        ids.append(pid)
        last = score
    return ids


def aggregate(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["domain"], []).append(row["value"])
    return sum(sum(v) / len(v) for v in groups.values()) / len(groups), {
        k: sum(v) / len(v) for k, v in groups.items()
    }
