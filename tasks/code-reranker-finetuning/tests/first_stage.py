"""Freeze the full RRF union of BM25 Top-200 and local BGE Top-200."""

from collections import Counter, defaultdict
import json
from pathlib import Path
import re

import numpy as np
import torch

MODEL_DIR = Path("/task/models/bge-base-en-v1.5")
EMBED_BATCH_SIZE = 32
EMBED_MAX_LENGTH = 512
CORPUS = Path("/task/data/corpus.jsonl")
QUERIES = Path("/tests/data/queries.jsonl")
OUTPUT = Path("/logs/verifier/.private/first_stage_retrieval.jsonl")
BRANCH_K = 200
RRF_K = 60
BM25_K1 = 1.2
BM25_B = 0.75


def load_encoder():
    from transformers import AutoModel, AutoTokenizer

    if not MODEL_DIR.is_dir():
        raise FileNotFoundError(f"missing embedding checkpoint directory: {MODEL_DIR}")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR, local_files_only=True, trust_remote_code=False,
    )
    model = AutoModel.from_pretrained(
        MODEL_DIR, local_files_only=True, trust_remote_code=False, use_safetensors=True,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.float().eval().to(device)
    return tokenizer, model


def embed(texts, tokenizer, model):
    if not texts:
        raise ValueError("no texts to embed")
    vectors = []
    with torch.inference_mode():
        for start in range(0, len(texts), EMBED_BATCH_SIZE):
            encoded = tokenizer(
                texts[start:start + EMBED_BATCH_SIZE], padding=True,
                truncation=True, max_length=EMBED_MAX_LENGTH, return_tensors="pt",
            )
            encoded = {name: value.to(model.device) for name, value in encoded.items()}
            # BGE uses the first token (CLS); no query instruction is prepended.
            outputs = model(**encoded).last_hidden_state[:, 0, :]
            vectors.append(outputs.float().cpu().numpy())
    array = np.concatenate(vectors, axis=0)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError("invalid local embedding result")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if (norms == 0).any() or not np.isfinite(norms).all():
        raise ValueError("zero-length or non-finite embedding norm")
    return array / norms


def candidates(doc_ids, doc_vectors, queries, query_vectors, k=BRANCH_K):
    if len(set(doc_ids)) != len(doc_ids) or len(doc_ids) < k:
        raise ValueError("corpus has too few distinct IDs")
    scores = query_vectors @ doc_vectors.T
    for query, row in zip(queries, scores):
        ranked = sorted(range(len(doc_ids)), key=lambda i: (-float(row[i]), doc_ids[i]))
        yield {"qid": query["_id"], "docids": [doc_ids[i] for i in ranked[:k]]}


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_candidates(corpus, queries, k=BRANCH_K):
    doc_ids = [doc["_id"] for doc in corpus]
    if len(set(doc_ids)) != len(doc_ids) or len(doc_ids) < k:
        raise ValueError("corpus has too few distinct IDs")
    counts = [Counter(tokenize((doc.get("title", "") + " " + doc["text"]).strip()))
              for doc in corpus]
    lengths = np.asarray([sum(count.values()) for count in counts], dtype=np.float64)
    avg_length = float(lengths.mean()) or 1.0  # empty-token corpus yields zero scores
    length_norm = BM25_K1 * (1 - BM25_B + BM25_B * lengths / avg_length)
    postings = defaultdict(list)
    for index, count in enumerate(counts):
        for term, frequency in count.items():
            postings[term].append((index, frequency))
    weights = {}
    for term, entries in postings.items():
        indices = np.asarray([entry[0] for entry in entries])
        tf = np.asarray([entry[1] for entry in entries], dtype=np.float64)
        idf = np.log1p((len(corpus) - len(entries) + 0.5) / (len(entries) + 0.5))
        weights[term] = (indices, idf * tf * (BM25_K1 + 1) / (tf + length_norm[indices]))
    for query in queries:
        scores = np.zeros(len(corpus), dtype=np.float64)
        for term in sorted(set(tokenize(query["text"]))):
            if term in weights:
                indices, values = weights[term]
                scores[indices] += values
        ranked = sorted(range(len(doc_ids)), key=lambda i: (-float(scores[i]), doc_ids[i]))
        yield {"qid": query["_id"], "docids": [doc_ids[i] for i in ranked[:k]]}


def rrf_fuse(embedding_ids, bm25_ids):
    scores = defaultdict(float)
    for branch in (embedding_ids, bm25_ids):
        if len(set(branch)) != len(branch):
            raise ValueError("duplicate ID within an RRF branch")
        for rank, doc_id in enumerate(branch, 1):
            scores[doc_id] += 1.0 / (RRF_K + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def hybrid_candidates(corpus, doc_vectors, queries, query_vectors):
    dense = candidates([doc["_id"] for doc in corpus], doc_vectors, queries, query_vectors)
    lexical = bm25_candidates(corpus, queries)
    for embedding, bm25 in zip(dense, lexical, strict=True):
        if embedding["qid"] != bm25["qid"]:
            raise ValueError("retrieval branches disagree on query order")
        yield {"qid": embedding["qid"], "embedding_docids": embedding["docids"],
               "bm25_docids": bm25["docids"],
               "docids": rrf_fuse(embedding["docids"], bm25["docids"])}


def main():
    tokenizer, model = load_encoder()
    with CORPUS.open(encoding="utf-8") as handle:
        corpus = [json.loads(line) for line in handle if line.strip()]
    with QUERIES.open(encoding="utf-8") as handle:
        queries = [json.loads(line) for line in handle if line.strip()]
    texts = [(doc.get("title", "") + " " + doc["text"]).strip()[:512] for doc in corpus]
    doc_vectors = embed(texts, tokenizer, model)
    query_vectors = embed([q["text"][:512] for q in queries], tokenizer, model)
    results = list(hybrid_candidates(corpus, doc_vectors, queries, query_vectors))
    OUTPUT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(row) + "\n" for row in results), encoding="utf-8")
    OUTPUT.chmod(0o600)


if __name__ == "__main__":
    main()
