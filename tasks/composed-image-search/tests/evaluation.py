import math, json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def ap(ids, gold, k):
    positives = {i for i, v in gold.items() if v > 0}
    if not positives:
        return 0.0
    hit = 0
    total = 0.0
    for rank, i in enumerate(ids[:k], 1):
        if i in positives:
            hit += 1
            total += hit / rank
    return total / min(k, len(positives))


def composed_map(ids, gold, k=50):
    return sum(ap(ids, gold, k) for k in [5, 10, 25, 50]) / 4


def quality(ids, gold, group):
    if group == "relative":
        positives = {i for i, v in gold.items() if v > 0}
        return sum(float(bool(set(ids[:k]) & positives)) for k in [1, 5, 10, 50]) / 4
    return composed_map(ids, gold)


def validate(q, p, pages):
    if not isinstance(p, dict) or p.get("query_id") != q["query_id"]:
        raise ValueError("Query ID mismatch")
    rows = p.get("results")
    if not isinstance(rows, list) or len(rows) > 50:
        raise ValueError("Expected at most50 images")
    ids = []
    last = math.inf
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid result")
        pid = row.get("image_id")
        score = row.get("score")
        if (
            not isinstance(pid, str)
            or pid not in pages
            or pid == q["reference_image_id"]
            or pid in ids
        ):
            raise ValueError("Invalid, duplicate or reference image")
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
    for x in rows:
        groups.setdefault(x["domain"], []).append(x["value"])
    values = {k: sum(v) / len(v) for k, v in groups.items()}
    return sum(values.values()) / len(values), values
