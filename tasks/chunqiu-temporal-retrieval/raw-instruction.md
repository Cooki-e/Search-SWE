# ChunQiu Temporal Retrieval

## Goal and inputs

Build an executable system to retrieve original event records from Classical
Chinese annals for a requested reign, year, month or time window. Rank event
records and distinguish them from later commentary discussing the same period.
Return up to ten corpus documents per query.

- Corpus: `/task/data/corpus.jsonl`.
- Labeled examples: `/task/data/examples.jsonl`.
- Dated corpus examples: `/task/data/dated_examples.jsonl`.
- Local model: `/task/models/Qwen3-Embedding-0.6B`.
- Read `/task/docs/environment.md` and `/task/docs/available_resources.md` for
  the runtime and complete model/provider/endpoint policy.

## Resources and restrictions

Development budget: 6 hours. One NVIDIA A100 40GB, 16 CPU cores, 32 GiB RAM,
100 GiB storage. Only the documented APIs are permitted, for the supplied task
material. No hidden questions/judgments, external datasets/documents, external
search or additional pretrained weights. No precomputed or hard-coded
query-to-answer mappings. Keep credentials out of source, logs and artifacts.

## Submission

Submit executable `/app/build.sh`, `/app/run.sh`, and all runtime dependencies
under `/app`. Installed packages and live development processes are not
transferred. `/task` is read-only. Verification uses a separate environment and
an unprivileged user, with `/app` read-only. The corpus, model and docs remain
available; neither examples file is mounted there. Use the supplied index
directory for generated files and the requested output path for results;
do not require another fixed writable path.

## Build and initialization

`/app/build.sh --corpus /task/data/corpus.jsonl --index-dir /app/index`

The actual index path may vary and starts empty. Complete indexing and all
initialization, including any resident service, and exit zero within 1,200
seconds. Query inputs are supplied only after successful initialization.

## Batch queries and output

`/app/run.sh --index-dir /app/index --queries /path/to/queries.jsonl --output /path/to/results.jsonl --top-k 10`

Read `query_id` and `text` from each query. Write exactly one UTF-8 JSONL result
per query, preserving its ID, in any query order:
`{"query_id":"query-id","results":[{"doc_id":"document-id","score":0.123}]}`.
Return zero to ten distinct corpus IDs with finite numeric scores, sorted by
descending score; ties follow corpus order. Empty lists are valid.

The verifier submits the complete hidden query batch in one invocation.
Batching is allowed. Finish with exit status zero within 120 seconds, including
input processing, encoding, retrieval, reranking, API waiting and output writing.

## Evaluation

Maximize mean nDCG@10 on the hidden test set. Build or batch timeouts, command
failures, missing or invalid output, or integrity violations give score zero.
