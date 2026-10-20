"""Document-scoped evidence-page set validation and F1."""

import math, json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def page_set_f1(ids, qrels, k=10):
    relevant = {x for x, v in qrels.items() if v > 0}
    returned = set(ids[:k])
    return (
        2 * len(returned & relevant) / (len(returned) + len(relevant))
        if returned or relevant
        else 0.0
    )


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
        pid = row.get("page_id")
        score = row.get("score")
        if (
            not isinstance(pid, str)
            or pid not in pages
            or pages[pid]["domain"] != q["domain"]
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
        if q.get("doc_id") is not None and pages[pid].get("doc_id") != q["doc_id"]:
            raise ValueError("Page belongs to a different document")
        ids.append(pid)
        last = score
    return ids


def aggregate(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["domain"], []).append(row["value"])
    return sum(x["value"] for x in rows) / len(rows), {
        k: sum(v) / len(v) for k, v in groups.items()
    }


def validate_inputs(queries, labels, pages):
    if not pages or not queries:
        raise ValueError("Empty page corpus or query set")
    keys = [q.get("query_id") for q in queries]
    if any(not isinstance(k, str) or not k for k in keys) or len(set(keys)) != len(
        keys
    ):
        raise ValueError("Invalid or duplicate query IDs")
    gold = {}
    for row in labels:
        key = row.get("query_id")
        if key in gold:
            raise ValueError("Duplicate label query ID")
        gold[key] = row.get("qrels")
    if set(gold) != set(keys):
        raise ValueError("Query and label coverage differ")
    docs = {(p.get("domain"), p.get("doc_id")) for p in pages.values()}
    for q in queries:
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            raise ValueError("Empty question")
        if (q.get("domain"), q.get("doc_id")) not in docs:
            raise ValueError("Unknown query document/domain")
        rel = gold[q["query_id"]]
        if not isinstance(rel, dict) or not rel:
            raise ValueError("Missing evidence labels")
        positives = 0
        for pid, value in rel.items():
            if pid not in pages or (
                pages[pid].get("domain"),
                pages[pid].get("doc_id"),
            ) != (q["domain"], q["doc_id"]):
                raise ValueError("Evidence refers to an unknown or different document")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("Invalid evidence relevance")
            positives += value > 0
        if not 1 <= positives <= 10:
            raise ValueError("Evidence set does not fit output budget")
    return gold
