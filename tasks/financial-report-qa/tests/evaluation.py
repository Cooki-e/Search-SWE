"""Deterministic source-location validation and Evidence Recall@5."""

import json
from pathlib import Path


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate_prediction(query, prediction, documents):
    if not isinstance(prediction, dict) or set(prediction) != {"query_id", "spans"}:
        raise ValueError("Expected query_id and spans")
    if prediction["query_id"] != query["query_id"]:
        raise ValueError("Query identifier mismatch")
    spans = prediction["spans"]
    if not isinstance(spans, list) or len(spans) > 5:
        raise ValueError("Return at most five spans")
    for span in spans:
        if not isinstance(span, dict) or set(span) != {"document_id", "start", "end"}:
            raise ValueError("Invalid evidence fields")
        did, a, b = span["document_id"], span["start"], span["end"]
        if not isinstance(did, str) or did not in documents:
            raise ValueError("Unknown report")
        if (
            type(a) is not int
            or type(b) is not int
            or not 0 <= a < b <= len(documents[did])
            or b - a > 512
        ):
            raise ValueError("Invalid Unicode character range")
    return spans


def merged_ranges(spans):
    by_document = {}
    for span in spans[:5]:
        by_document.setdefault(span["document_id"], []).append(
            (span["start"], span["end"])
        )
    merged = {}
    for did, ranges in by_document.items():
        out = []
        for a, b in sorted(ranges):
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(b, out[-1][1]))
            else:
                out.append((a, b))
        merged[did] = out
    return merged


def evidence_recall(gold, spans):
    evidence = gold["evidence"]
    if not evidence or len({e["evidence_id"] for e in evidence}) != len(evidence):
        raise ValueError("Invalid gold evidence units")
    ranges = merged_ranges(spans)
    hit_ids = []
    for fact in evidence:
        locations = fact["locations"]
        if not locations:
            raise ValueError("Gold fact has no location")
        if any(
            any(
                a <= loc["start"] and b >= loc["end"]
                for a, b in ranges.get(loc["document_id"], [])
            )
            for loc in locations
        ):
            hit_ids.append(fact["evidence_id"])
    return len(hit_ids) / len(evidence), hit_ids


def evaluate_rows(queries, predictions, labels, documents):
    counts = {}
    by_id = {}
    for prediction in predictions:
        qid = prediction.get("query_id") if isinstance(prediction, dict) else None
        if isinstance(qid, str):
            counts[qid] = counts.get(qid, 0) + 1
            by_id[qid] = prediction
    details = []
    for query in queries:
        qid = query["query_id"]
        row = {
            "query_id": qid,
            "recall": 0.0,
            "matched_evidence": [],
            "gold_evidence_count": len(labels[qid]["evidence"]),
        }
        try:
            if counts.get(qid) != 1:
                raise ValueError("Missing or duplicated query result")
            spans = validate_prediction(query, by_id[qid], documents)
            row["recall"], row["matched_evidence"] = evidence_recall(labels[qid], spans)
        except (ValueError, TypeError, KeyError) as exc:
            row["error"] = str(exc)
        details.append(row)
    return sum(row["recall"] for row in details) / len(queries), details
