import json, math


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def quality(ids, gold, junk):
    ids = [i for i in ids if i not in set(junk)][:5]
    positive = {i for i, v in gold.items() if v > 0}
    ideal = sum(1 / math.log2(i + 2) for i in range(min(5, len(positive))))
    return (
        sum(1 / math.log2(i + 2) for i, p in enumerate(ids) if p in positive) / ideal
        if ideal
        else 0.0
    )


def validate(q, p, pages):
    if not isinstance(p, dict) or p.get("query_id") != q["query_id"]:
        raise ValueError("Query ID mismatch")
    rows = p.get("results")
    if not isinstance(rows, list) or len(rows) > 5:
        raise ValueError("Expected at most5 results")
    ids = []
    last = math.inf
    for x in rows:
        if (
            not isinstance(x, dict)
            or x.get("image_id") not in pages
            or x["image_id"] in ids
            or x["image_id"] in q.get("exclude_image_ids", [])
        ):
            raise ValueError("Invalid or duplicate image")
        v = x.get("score")
        if (
            isinstance(v, bool)
            or not isinstance(v, (float, int))
            or not math.isfinite(v)
            or v > last
        ):
            raise ValueError("Invalid ranking score")
        ids.append(x["image_id"])
        last = v
    return ids


def aggregate(rows):
    groups = {}
    for x in rows:
        groups.setdefault(x["domain"], []).append(x["value"])
    scores = {k: sum(v) / len(v) for k, v in groups.items()}
    return sum(scores.values()) / len(scores), scores
