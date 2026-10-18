"""Pure input checks and Memora's released atomic-criterion FAMA aggregation."""

import json, math
from pathlib import Path


def jsonl(path):
    with Path(path).open() as f:
        return [json.loads(x) for x in f if x.strip()]


def corpus(path):
    p = Path(path)
    rows = jsonl(p / "records.jsonl" if p.is_dir() else p)
    out = {r["record_id"]: r for r in rows}
    if len(out) != len(rows):
        raise ValueError("Duplicate corpus ID")
    return out


def check_retrieval(q, p, records):
    if (
        not isinstance(p, dict)
        or set(p) != {"query_id", "record_ids"}
        or p["query_id"] != q["query_id"]
    ):
        raise ValueError("Invalid retrieval fields or query ID")
    ids = p["record_ids"]
    if (
        not isinstance(ids, list)
        or len(ids) > 350
        or any(not isinstance(i, str) for i in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("Return up to 350 unique record IDs")
    for i in ids:
        r = records.get(i)
        if (
            not r
            or r["persona_id"] != q["persona_id"]
            or r["session_id"] > q["cutoff_session"]
        ):
            raise ValueError("Unknown, wrong-persona or future record")
    return ids


def answer_request(q, ids, records):
    return dict(q, records=[dict(records[i]) for i in ids])


def check_answer(q, p):
    if (
        not isinstance(p, dict)
        or set(p) != {"query_id", "answer"}
        or p["query_id"] != q["query_id"]
    ):
        raise ValueError("Invalid answer fields or query ID")
    if not isinstance(p["answer"], str) or not p["answer"].strip():
        raise ValueError("Empty answer")
    return {"query_id": q["query_id"], "answer": p["answer"]}


def fama(gold, panels):
    cs = gold["criteria"]
    if len(panels) != 3 or any(
        len(p) != len(cs) or any(v not in ["yes", "no"] for v in p) for p in panels
    ):
        raise ValueError("Incomplete atomic judge votes")
    decisions = [
        "yes" if sum(p[i] == "yes" for p in panels) >= 2 else "no"
        for i in range(len(cs))
    ]
    m = [i for i, c in enumerate(cs) if c["kind"] == "memory_presence"]
    f = [i for i, c in enumerate(cs) if c["kind"] == "forgetting_absence"]
    if not m or len(m) + len(f) != len(cs):
        raise ValueError("Invalid criterion kinds")
    mpa = sum(decisions[i] == cs[i]["expected_answer"] for i in m) / len(m)
    faa = (
        sum(decisions[i] == cs[i]["expected_answer"] for i in f) / len(f) if f else 1.0
    )
    lam = len(f) / len(cs)
    return max(0.0, mpa - lam * (1 - faa)), {
        "mpa": mpa,
        "faa": faa,
        "forgetting_weight": lam,
        "decisions": decisions,
    }
