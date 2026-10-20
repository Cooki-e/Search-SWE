import math, json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def iou(a, b):
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    return inter / (a[1] - a[0] + b[1] - b[0] - inter)


def utility(x):
    return 0.7 * sum(x >= t for t in [0.5, 0.7, 0.9]) / 3 + 0.3 * x


def quality(window, gold):
    x = max(iou(window, g) for g in gold["windows"])
    upper = gold["upper_bound"]
    if not 0 < upper <= 1 + 1e-8:
        raise ValueError("Invalid private upper bound")
    value = utility(x) / upper
    if value > 1 + 1e-6:
        raise ValueError("Private upper bound underestimated")
    return min(1.0, value)


def validate(q, p, pages):
    if not isinstance(p, dict) or p.get("query_id") != q["query_id"]:
        raise ValueError("Query ID mismatch")
    grid = pages[q["video_id"]]["grid"]
    window = []
    for key in ["start", "end"]:
        value = p.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("Invalid time")
        closest = min(grid, key=lambda x: abs(x - value))
        if abs(closest - value) > 1e-6:
            raise ValueError("Endpoint outside legal grid")
        window.append(closest)
    if window[0] >= window[1]:
        raise ValueError("Empty or reversed interval")
    return window


def aggregate(rows):
    groups = {}
    for x in rows:
        groups.setdefault(x["domain"], []).append(x["value"])
    scores = {k: sum(v) / len(v) for k, v in groups.items()}
    return sum(scores.values()) / len(scores), scores
