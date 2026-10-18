"""Page-ranking contract and linear graded nDCG@10."""

import math, json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def ndcg(ids, qrels, k=10):
    gains = [float(qrels.get(x, 0)) for x in ids[:k]]
    ideal = sorted((float(v) for v in qrels.values()), reverse=True)[:k]
    dcg = sum(v / math.log2(i + 2) for i, v in enumerate(gains))
    idcg = sum(v / math.log2(i + 2) for i, v in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


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
        pid = row.get("doc_id")
        score = row.get("score")
        if (
            not isinstance(pid, str)
            or pid not in pages
            or pages[pid].get("domain", "movie") != q.get("domain", "movie")
            or pid in ids
        ):
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
    return sum(row["value"] for row in rows) / len(rows), {
        k: sum(v) / len(v) for k, v in groups.items()
    }
