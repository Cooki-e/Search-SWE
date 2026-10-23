# Lightweight query retrieval

## Objective and inputs

Process batches of search queries. Return up
to ten ranked documents from each query's specified collection, while meeting
a fixed retrieval-quality threshold and minimizing complete query-processing
time. Use the supplied resources; no particular implementation is required.

- Corpus: `/task/data/corpus.jsonl`, 66,454 documents in three collections.
- Examples: `/task/data/examples.jsonl`, 80,000 labeled examples.
- Base model: `/task/models/Llama-3.2-1B`.
- Environment and resources: `/task/docs/environment.md` and
  `/task/docs/available_resources.md`.
- No network or external APIs. No external datasets, additional pretrained
  weights, hidden labels, precomputed test answers or hard-coded answer mappings.

## Resources and artifacts

Six hours of development; one NVIDIA A100 40GB, 16 CPU cores, 32 GiB RAM and
100 GiB storage. Submit all required files under `/app`, including executable
`build.sh` and `run.sh`. Only this directory transfers to the separate verifier.
Development processes and installed packages do not transfer. Corpus, base model
and resource documents remain available; examples do not. `/app` and `/task`
are read-only. Use the index directory during build and `$TMPDIR` at runtime.

## Interface

```bash
/app/build.sh --corpus /task/data/corpus.jsonl --index-dir /path/to/index
/app/run.sh --index-dir /path/to/index --serve
```

Build into the initially empty index directory within 1,200 seconds and exit
zero. The index is read-only afterwards. Service startup has 120 seconds and
must emit exactly one readiness JSON line: `{"status":"ready"}`. Keep the
process running and handle each following stdin JSON line with one stdout JSON
line. Logs go to stderr.

Request: `{"queries":[{"query_id":"request-id","collection":"corpus1","text":"query text","instruction":"retrieval instruction"}],"top_k":10}`.
Response: `{"results":[{"query_id":"request-id","results":[{"doc_id":"document-id","score":1.0}]}]}`.
Cover every query exactly once, in any query order. Each document list contains
at most ten distinct, valid IDs from its query's collection, with finite numeric
scores in descending order. Ties may retain the returned order.

## Timing and score

Warm-up uses supplied example queries and has 60 seconds. Then all 1,271 hidden queries arrive in
one batch, which must complete within 120 seconds. Timing includes receiving
and processing queries, retrieval, ranking and returning the response. Build,
model loading and warm-up are excluded. Use three fresh service instances with
fresh temporary storage; aggregate by median retrieval time.

Quality is original graded nDCG@10, with relevance grades used directly as gains
and an equal mean across the three collections. Every timed run must reach
0.45. Below this threshold the score is zero. Valid submissions meeting this
requirement earn higher scores for lower median retrieval times. A median time
of 0.8 seconds or more earns zero.
