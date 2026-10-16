# Quantity-aware Retrieval

## Goal

Build an executable clinical-passage retrieval system using MedQuant. Return at most ten corpus documents that address a natural-language query and its numerical condition, ranked by relevance.

## Inputs

- `/task/data/corpus.jsonl`: the searchable collection.
- `/task/data/examples.jsonl`: labeled examples.
- `/task/models/Qwen3-Embedding-0.6B`: read-only model files.
- `/task/docs/environment.md` and `/task/docs/available_resources.md` are normative, read-only runtime/resource documentation.

## Resources and integrity

Development has a 6-hour budget. The runtime provides one NVIDIA A100 40GB, 16 CPU cores, 32 GiB RAM and 100 GiB storage.

Follow the exact model/provider/endpoint policy in the resource documents. API use is restricted to the supplied task material. No external corpus, benchmark answers, hidden labels/questions, external datasets, search services, precomputed query-answer files, hard-coded query-answer mappings, or additional pretrained weights. Do not expose credentials in code/logs/artifacts.

All submission files and runtime dependencies belong under `/app`; `/task` is read-only. In verification `/app` is read-only, execution uses an unprivileged user, and only the supplied index directory and requested result path are writable. Corpus/model/docs remain mounted; `examples.jsonl` does not. Agent-installed packages and live processes are not transferred.

## Build

Executable `/app/build.sh --corpus /task/data/corpus.jsonl --index-dir /app/index`.

The actual index path can differ and starts empty. Complete all initialization and exit 0 within 1,200 seconds. Query invocations begin only after a successful build. Do not require another fixed writable path.

## Query and output

Executable `/app/run.sh --index-dir /app/index --queries /path/to/queries.jsonl --output /path/to/results.jsonl --top-k 10`.

Read `query_id` and `text` from each input query and produce exactly one UTF-8 JSONL object per query: `{"query_id":"query-id","results":[{"doc_id":"document-id","score":0.123}]}`. Preserve the supplied query ID. Return 0–10 unique corpus IDs with finite numeric scores, descending by score and using corpus order for ties. Empty lists are valid.

Each query has a 5-second time limit. A timeout scores zero for that query.

## Metric and failure behavior

Retrieval quality is evaluated by mean nDCG@10 on a hidden test set. Maximize this metric to improve the final score.

Build failures, other execution errors, invalid output or integrity violations result in a task score of zero. Resource and model/provider/endpoint/credential restrictions apply throughout.
