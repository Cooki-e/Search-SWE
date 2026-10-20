import json, math


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def validate(query, pred, docs):
    if not isinstance(pred, dict) or pred.get("query_id") != query["query_id"]:
        raise ValueError("Invalid query identifier")
    if not isinstance(pred.get("answer"), str) or not pred["answer"].strip():
        raise ValueError("Missing answer text")
    pages = pred.get("pages", [])
    if (
        not isinstance(pages, list)
        or any(
            type(p) is not int or p < 1 or p > docs[query["doc_id"]]["page_count"]
            for p in pages
        )
        or len(set(pages)) != len(pages)
    ):
        raise ValueError("Invalid cited pages")
    return pred["answer"], pages


def aggregate(rows):
    by = {}
    for row in rows:
        by.setdefault(row["branch"], []).append(row["value"])
    means = {k: sum(v) / len(v) for k, v in by.items()}
    return sum(means.values()) / len(means) if means else 0.0, means
