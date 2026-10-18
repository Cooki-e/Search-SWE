Build a search system for users who recall a work through scattered details. A request may contain a long description, comparisons, uncertain memories and background information. Return documents from the supplied collection.

The collection is at `/task/data/corpus/records.jsonl`. Each row contains `doc_id`, `title` and the full article `text`.

Create executable `/app/build.sh` and `/app/run.sh`, with their supporting files under `/app`:
`/app/build.sh --corpus /task/data/corpus --index-dir /work/index` `/app/run.sh --index-dir /work/index --queries /work/input/queries.jsonl --output /work/output/results.jsonl`

Each input JSONL row contains `query_id` and `question`. Return the same `query_id` and a `results` list of at most ten distinct documents, each with `doc_id` and a finite numeric `score`, in descending score order. Write diagnostics to stderr.

Public queries and relevance labels are at `/task/data/validation/queries.jsonl` and `/task/data/validation/labels.jsonl`. Labels contain `query_id` and `qrels`, a mapping of document IDs to relevance grades. Original sentence-level annotations for these public queries are at `/task/data/training/sentence_labels.jsonl`. The remaining queries and labels are not supplied.

The environment has 8 CPU cores, 32 GiB RAM and 100 GiB storage, without a GPU. The OpenRouter and Jina APIs listed in the resource document are available. Development has a two-hour budget, index construction up to 60 minutes, and the query workload described below. Calls may be repeated with different input files. Data and documentation mounts are read-only; write generated indexes to the supplied index directory.

During verification, build and query commands run as a non-root user. The implementation under `/app` and the supplied inputs are read-only. The passed index directory already exists and is writable, but its parent directory is not writable. Create build files, caches and temporary directories inside that index directory or the supplied `TMPDIR`; do not create sibling directories or rename the index directory itself. The index persists and remains writable across query calls. Write results at the passed output path, whose parent directory is writable. Honor `TMPDIR` and `XDG_CACHE_HOME` rather than writing to `/app` or assuming a writable system temporary directory.

Read `/task/docs/environment.md` and `/task/docs/available_resources.md` before starting. Evaluation checks executable behavior, result validity and relevance on held-out queries, together with the resource and API rules. It runs in a separate environment with the submitted `/app` files and supplied corpus.

The system must handle workloads of up to 450 requests in 2 calls of at most 225 requests. Each call has an independent 2,700-second allowance; time used by one call does not reduce another. Completed valid JSONL rows remain usable if a query call times out; missing or malformed rows are unsuccessful. A failed query command other than a timeout invalidates that call.

You may use the public examples to implement and check the complete build and query path during development. Include all required implementation files under `/app` so the system runs after a fresh start with the supplied inputs.
