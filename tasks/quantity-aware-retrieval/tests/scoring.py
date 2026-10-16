"""Pure deterministic output validation and binary nDCG@10."""
import json
import math


class VerificationError(ValueError):
    pass


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise VerificationError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise VerificationError(f"Non-finite JSON constant: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)


def validate_row(row, query_id, corpus_order, top_k=10):
    if not isinstance(row, dict) or row.get("query_id") != query_id:
        raise VerificationError("Missing or mismatched query_id")
    results = row.get("results")
    if not isinstance(results, list) or len(results) > top_k:
        raise VerificationError(f"results must contain at most {top_k} items")
    ids, previous = [], None
    for item in results:
        if not isinstance(item, dict):
            raise VerificationError("Result item is not an object")
        doc_id, score = item.get("doc_id"), item.get("score")
        if not isinstance(doc_id, str) or doc_id not in corpus_order:
            raise VerificationError("Unknown document ID")
        if doc_id in ids:
            raise VerificationError("Duplicate document ID")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise VerificationError("Score must be numeric")
        try:
            number = float(score)
        except (OverflowError, ValueError):
            raise VerificationError("Score is not finite")
        if not math.isfinite(number):
            raise VerificationError("Score is not finite")
        key = (-number, corpus_order[doc_id])
        if previous is not None and key < previous:
            raise VerificationError("Results must be score-descending; ties use corpus order")
        previous = key
        ids.append(doc_id)
    return ids


def ndcg_at_10(ids, relevant):
    if not relevant:
        raise VerificationError("Reference relevant set is empty")
    discounts = [1 / math.log2(rank + 2) for rank in range(10)]
    ideal = sum(discounts[:min(10, len(relevant))])
    return sum(weight for doc, weight in zip(ids[:10], discounts) if doc in relevant) / ideal


def normalized_reward(raw, baseline):
    if not math.isfinite(raw) or not 0 <= raw <= 1 or not 0 <= baseline < 1:
        raise VerificationError("Invalid metric or baseline")
    return max(0.0, min(1.0, (raw - baseline) / (1.0 - baseline)))
