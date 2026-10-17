#!/usr/bin/env python3
"""Evaluate a submitted code reranker checkpoint against its unmodified backbone."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from first_stage import BRANCH_K, RRF_K, rrf_fuse

BACKBONE_PATH = Path("/task/models/bge-reranker-base")
MODEL_PATH = Path("/app/output/model")
CORPUS_PATH = Path("/task/data/corpus.jsonl")
QUERIES_PATH = Path("/tests/data/queries.jsonl")
GROUND_TRUTH_PATH = Path("/tests/data/ground_truth.jsonl")
FIRST_STAGE_PATH = Path("/logs/verifier/.private/first_stage_retrieval.jsonl")
REPORT_PATH = Path("/logs/verifier/report.json")
MAX_LENGTH = 512
BATCH_SIZE = 16

_NON_STRUCTURAL_CONFIG_FIELDS = {
    "_name_or_path",
    "finetuning_task",
    "id2label",
    "label2id",
    "problem_type",
    "torch_dtype",
    "transformers_version",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no records")
    return rows


def required_text(row: dict[str, Any], field: str, location: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}: missing non-empty {field!r}")
    return value.strip()


def document_text(row: dict[str, Any], location: str) -> str:
    text = f"{row.get('title', '')} {row.get('text', '')}".strip()
    if not text:
        raise ValueError(f"{location}: empty document text")
    return text


def load_evaluation_data() -> tuple[dict[str, str], list[str], list[str], dict[str, set[str]], dict[str, list[str]]]:
    corpus_rows = read_jsonl(CORPUS_PATH)
    corpus: dict[str, str] = {}
    for index, row in enumerate(corpus_rows, 1):
        doc_id = required_text(row, "_id", f"{CORPUS_PATH}:{index}")
        if doc_id in corpus:
            raise ValueError("corpus contains duplicate document IDs")
        corpus[doc_id] = document_text(row, f"{CORPUS_PATH}:{index}")

    query_rows = read_jsonl(QUERIES_PATH)
    query_ids = [required_text(row, "_id", f"{QUERIES_PATH}:{index}") for index, row in enumerate(query_rows, 1)]
    if len(set(query_ids)) != len(query_ids):
        raise ValueError("queries contain duplicate query IDs")
    query_texts = [required_text(row, "text", f"{QUERIES_PATH}:{index}") for index, row in enumerate(query_rows, 1)]

    labels: dict[str, set[str]] = {}
    for index, row in enumerate(read_jsonl(GROUND_TRUTH_PATH), 1):
        query_id = required_text(row, "query_id", f"{GROUND_TRUTH_PATH}:{index}")
        doc_ids = row.get("relevant_doc_ids")
        if not isinstance(doc_ids, list) or not doc_ids or not all(isinstance(doc_id, str) and doc_id for doc_id in doc_ids):
            raise ValueError(f"{GROUND_TRUTH_PATH}:{index}: invalid relevant_doc_ids")
        if query_id in labels:
            raise ValueError(f"{GROUND_TRUTH_PATH}:{index}: duplicate query ID")
        labels[query_id] = set(doc_ids)
    if set(query_ids) != set(labels):
        raise ValueError("queries and ground truth do not cover the same query IDs")
    unknown_docs = set().union(*labels.values()) - set(corpus)
    if unknown_docs:
        raise ValueError(f"ground truth references documents outside the corpus: {sorted(unknown_docs)[:3]}")

    candidates: dict[str, list[str]] = {}
    for index, row in enumerate(read_jsonl(FIRST_STAGE_PATH), 1):
        query_id = required_text(row, "qid", f"{FIRST_STAGE_PATH}:{index}")
        for field, minimum, maximum in (("embedding_docids", BRANCH_K, BRANCH_K),
                                         ("bm25_docids", BRANCH_K, BRANCH_K),
                                         ("docids", BRANCH_K, 2 * BRANCH_K)):
            doc_ids = row.get(field)
            if not isinstance(doc_ids, list) or not minimum <= len(doc_ids) <= maximum:
                raise ValueError(f"{FIRST_STAGE_PATH}:{index}: expected {minimum}..{maximum} IDs in {field}")
            if not all(isinstance(doc_id, str) and doc_id for doc_id in doc_ids):
                raise ValueError(f"{FIRST_STAGE_PATH}:{index}: invalid candidate ID in {field}")
            if len(set(doc_ids)) != len(doc_ids) or any(doc_id not in corpus for doc_id in doc_ids):
                raise ValueError(f"{FIRST_STAGE_PATH}:{index}: unknown or duplicate candidate ID in {field}")
        if row["docids"] != rrf_fuse(row["embedding_docids"], row["bm25_docids"]):
            raise ValueError(f"{FIRST_STAGE_PATH}:{index}: candidates differ from the full ordered RRF union")
        if query_id in candidates:
            raise ValueError(f"{FIRST_STAGE_PATH}:{index}: duplicate query ID")
        candidates[query_id] = row["docids"]
    if set(query_ids) != set(candidates):
        raise ValueError("queries and first-stage retrieval do not cover the same query IDs")
    return corpus, query_ids, query_texts, labels, candidates


def config_signature(model: torch.nn.Module) -> dict[str, Any]:
    config = model.config.to_dict()
    for field in _NON_STRUCTURAL_CONFIG_FIELDS:
        config.pop(field, None)
    return config


def model_signature(model: torch.nn.Module) -> dict[str, Any]:
    return {
        "model_class": f"{type(model).__module__}.{type(model).__qualname__}",
        "config": config_signature(model),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "parameters": [(name, tuple(parameter.shape)) for name, parameter in model.named_parameters()],
    }


def require_matching_architecture(backbone: torch.nn.Module, submitted: torch.nn.Module) -> int:
    expected = model_signature(backbone)
    actual = model_signature(submitted)
    for field in ("model_class", "config", "parameter_count", "parameters"):
        if actual[field] != expected[field]:
            raise ValueError(f"submitted checkpoint does not match the backbone {field}")
    return int(expected["parameter_count"])


def load_checkpoint(path: Path) -> tuple[Any, torch.nn.Module]:
    if not path.is_dir():
        raise FileNotFoundError(f"missing checkpoint directory: {path}")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_safetensors=True)
    return tokenizer, model


def score_pairs(model: torch.nn.Module, tokenizer: Any, pairs: list[tuple[str, str]], device: torch.device) -> list[float]:
    scores: list[float] = []
    model.eval().to(device)
    with torch.inference_mode():
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start : start + BATCH_SIZE]
            encoded = tokenizer(
                [query for query, _ in batch],
                [document for _, document in batch],
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            encoded = {name: value.to(device) for name, value in encoded.items()}
            logits = model(**encoded).logits
            if logits.ndim != 2 or logits.shape[1] != 1:
                raise ValueError(f"reranker must produce one logit per pair, got shape {tuple(logits.shape)}")
            scores.extend(float(value) for value in logits[:, 0].float().cpu())
    if len(scores) != len(pairs):
        raise RuntimeError("reranker score count does not match pair count")
    if not all(math.isfinite(score) for score in scores):
        raise ValueError("reranker produced non-finite scores")
    return scores


def accuracy_at_5(
    model: torch.nn.Module,
    tokenizer: Any,
    corpus: dict[str, str],
    query_ids: list[str],
    query_texts: list[str],
    labels: dict[str, set[str]],
    candidates: dict[str, list[str]],
    device: torch.device,
) -> tuple[float, int]:
    pairs = [(query_text, corpus[doc_id]) for query_id, query_text in zip(query_ids, query_texts) for doc_id in candidates[query_id]]
    scores = score_pairs(model, tokenizer, pairs, device)
    hits = 0
    positive_not_in_pool = 0
    offset = 0
    for query_id in query_ids:
        doc_ids = candidates[query_id]
        local_scores = scores[offset : offset + len(doc_ids)]
        offset += len(doc_ids)
        if not labels[query_id].intersection(doc_ids):
            positive_not_in_pool += 1
            continue
        ranked_indexes = sorted(range(len(doc_ids)), key=lambda index: -local_scores[index])
        hits += int(any(doc_ids[index] in labels[query_id] for index in ranked_indexes[:5]))
    return hits / len(query_ids), positive_not_in_pool


def normalized_gain(baseline: float, submitted: float, ceiling: float) -> float:
    """Fraction of the fixed candidate pool's remaining Accuracy@5 headroom."""
    if not all(math.isfinite(value) for value in (baseline, submitted, ceiling)):
        raise ValueError("non-finite evaluation result")
    if not 0 <= baseline <= ceiling <= 1 or not 0 <= submitted <= ceiling:
        raise ValueError("accuracy exceeds the first-stage ceiling or is out of range")
    if ceiling == baseline:
        return 0.0
    return max(0.0, min(1.0, (submitted - baseline) / (ceiling - baseline)))


def write_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    corpus, query_ids, query_texts, labels, candidates = load_evaluation_data()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    backbone_tokenizer, backbone = load_checkpoint(BACKBONE_PATH)
    submitted_tokenizer, submitted = load_checkpoint(MODEL_PATH)
    for name in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "sentencepiece.bpe.model"):
        source = BACKBONE_PATH / name
        target = MODEL_PATH / name
        if not target.is_file() or target.is_symlink() or hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
            raise ValueError(f"tokenizer file differs from backbone: {name}")
    parameter_count = require_matching_architecture(backbone, submitted)

    baseline_accuracy, positive_not_in_pool = accuracy_at_5(
        backbone,
        backbone_tokenizer,
        corpus,
        query_ids,
        query_texts,
        labels,
        candidates,
        device,
    )
    del backbone, backbone_tokenizer
    if device.type == "cuda":
        torch.cuda.empty_cache()

    submitted_accuracy, submitted_positive_not_in_pool = accuracy_at_5(
        submitted,
        submitted_tokenizer,
        corpus,
        query_ids,
        query_texts,
        labels,
        candidates,
        device,
    )
    if submitted_positive_not_in_pool != positive_not_in_pool:
        raise RuntimeError("fixed first-stage candidate coverage changed during evaluation")
    improvement = submitted_accuracy - baseline_accuracy
    ceiling = (len(query_ids) - positive_not_in_pool) / len(query_ids)
    reward = normalized_gain(baseline_accuracy, submitted_accuracy, ceiling)
    report = {
        "valid": True,
        "dataset": "code-retrieval",
        "split": "test",
        "metric": "Accuracy@5",
        "query_count": len(query_ids),
        "retrieval": "BM25 + BGE, equal-weight RRF, full union",
        "branch_candidate_count": BRANCH_K,
        "rrf_k": RRF_K,
        "candidate_count_min": min(map(len, candidates.values())),
        "candidate_count_max": max(map(len, candidates.values())),
        "candidate_count_mean": sum(map(len, candidates.values())) / len(query_ids),
        "candidate_pair_count": sum(map(len, candidates.values())),
        "backbone_parameter_count": parameter_count,
        "positive_not_in_first_stage": positive_not_in_pool,
        "first_stage_accuracy_ceiling": ceiling,
        "remaining_headroom": ceiling - baseline_accuracy,
        "baseline_accuracy@5": baseline_accuracy,
        "submitted_accuracy@5": submitted_accuracy,
        "improvement": improvement,
        "reward": reward,
    }
    write_report(report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        report = {"valid": False, "reward": 0.0, "error": f"{type(error).__name__}: {error}"}
        write_report(report)
        print(report["error"], file=sys.stderr)
        raise SystemExit(1)
