#!/usr/bin/env python3
"""Deterministic output validation and MRR@10; no model judge or network."""

from __future__ import annotations

import json
import gzip
import math
from fractions import Fraction
from pathlib import Path


class InvalidSubmission(ValueError):
    pass


def load_queries(path: Path) -> list[dict[str, str]]:
    queries, seen = [], set()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            qid, text = row.get("query_id"), row.get("text", row.get("query"))
            if not isinstance(qid, str) or not qid or qid in seen:
                raise ValueError(f"{path}:{line_number}: missing/duplicate query ID")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{path}:{line_number}: empty query text")
            seen.add(qid)
            queries.append({"query_id": qid, "text": text})
    if not queries:
        raise ValueError("Query set must not be empty")
    return queries


def load_qrels(path: Path, query_ids: set[str]) -> dict[str, set[str]]:
    qrels = {qid: set() for qid in query_ids}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.split()
            if len(fields) != 4:
                raise ValueError(f"{path}:{line_number}: expected four TREC qrels fields")
            qid, _, docid, relevance = fields
            if qid in qrels and int(relevance) > 0:
                qrels[qid].add(docid)
    if any(not docs for docs in qrels.values()):
        raise ValueError("Every scored query needs a positive relevance judgment")
    return qrels


def validate_response(row: object, query_id: str, *, document_count: int) -> list[str]:
    if not isinstance(row, dict) or row.get("query_id") != query_id:
        raise InvalidSubmission("Response does not match the requested query ID")
    results = row.get("results")
    if not isinstance(results, list) or len(results) > 10:
        raise InvalidSubmission("results must be an array with at most ten hits")
    seen, ordered = set(), []
    previous = math.inf
    for hit in results:
        if not isinstance(hit, dict):
            raise InvalidSubmission("Each hit must be an object")
        docid, score = hit.get("doc_id"), hit.get("score")
        # prepare_corpus.py verifies that this corpus has precisely the IDs
        # 0..document_count-1. No corpus scan or large Python ID set is needed
        # during timed queries. Smoke fixtures must use the same ID convention.
        if (not isinstance(docid, str) or len(docid) > len(str(document_count - 1))
                or not docid.isascii() or not docid.isdigit()
                or str(int(docid)) != docid or not 0 <= int(docid) < document_count):
            raise InvalidSubmission("Unknown/noncanonical passage ID")
        if docid in seen:
            raise InvalidSubmission("Duplicate passage ID")
        try:
            finite = isinstance(score, (int, float)) and math.isfinite(score)
        except OverflowError:
            finite = False
        if isinstance(score, bool) or not finite or score > previous:
            raise InvalidSubmission("Scores must be finite and in descending order")
        previous = score
        seen.add(docid)
        ordered.append(docid)
    return ordered


def reciprocal_rank(docids: list[str], relevant: set[str]) -> Fraction:
    return next((Fraction(1, rank) for rank, docid in enumerate(docids[:10], 1)
                 if docid in relevant), Fraction(0))


def evaluate(rows: list[dict], queries: list[dict], qrels: dict[str, set[str]],
             *, document_count: int) -> dict:
    """Use every expected query in the denominator; absent results contribute zero."""
    query_ids = [query["query_id"] for query in queries]
    if not query_ids or len(set(query_ids)) != len(query_ids):
        raise ValueError("Expected queries must be nonempty and unique")
    if set(qrels) != set(query_ids) or any(not docs for docs in qrels.values()):
        raise ValueError("Qrels must cover exactly the expected query IDs")
    predictions = {}
    for row in rows:
        if not isinstance(row, dict):
            raise InvalidSubmission("Response must be an object")
        qid = row.get("query_id")
        if not isinstance(qid, str) or qid not in qrels or qid in predictions:
            raise InvalidSubmission("Unknown/duplicate output query ID")
        predictions[qid] = validate_response(row, qid, document_count=document_count)
    total = sum((reciprocal_rank(predictions.get(qid, []), qrels[qid])
                 for qid in query_ids), Fraction(0))
    mrr = total / len(query_ids)
    return {"mrr_at_10": float(mrr), "mrr_numerator": mrr.numerator,
            "mrr_denominator": mrr.denominator, "query_count": len(query_ids),
            "answered_query_count": len(predictions),
            "complete": len(predictions) == len(query_ids)}


def quality_passes(candidate: dict, reference: dict) -> bool:
    """Compare exact rational MRR, without rounding the reference to 0.1840."""
    return (candidate["complete"] and candidate["query_count"] == reference["query_count"]
            and Fraction(candidate["mrr_numerator"], candidate["mrr_denominator"])
            >= Fraction(reference["mrr_numerator"], reference["mrr_denominator"]))


def tradeoff_reward(candidate: dict, reference: dict, weights: dict[str, float]) -> float:
    """Candidate scoring formula; production weights require author calibration."""
    if set(weights) != {"quality", "time", "disk"}:
        raise ValueError("Weights must specify quality, time, and disk")
    if any(isinstance(w, bool) or not math.isfinite(w) or w <= 0 for w in weights.values()):
        raise ValueError("Weights must be finite and positive")
    if not quality_passes(candidate["quality"], reference["quality"]):
        return 0.0
    values = [candidate["quality"]["mrr_at_10"], reference["quality"]["mrr_at_10"],
              candidate["warm_seconds"], reference["warm_seconds"],
              candidate["index_bytes"], reference["index_bytes"]]
    if any(isinstance(v, bool) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Measured quality, time, and disk must be finite and positive")
    qm, qr, tm, tr, dm, dr = values
    log_u = (weights["quality"] * math.log(qm / qr)
             + weights["time"] * math.log(tr / tm)
             + weights["disk"] * math.log(dr / dm)) / sum(weights.values())
    if log_u >= 0:
        return 1 / (1 + math.exp(-log_u))
    exp_u = math.exp(log_u)
    return exp_u / (1 + exp_u)
