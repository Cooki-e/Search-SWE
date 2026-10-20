# Task: Visual-Document Question Answering

## Task Description

Build a system that answers questions using the supplied long documents. Relevant information may occur in body text, tables, charts or several pages. If the document does not contain the requested information, say so.

## Inputs and Available Validation Data

The collection is at `/task/data/corpus/`. Its `records.jsonl` contains `doc_id`, `pdf_path`, `text_path` and `page_count`. Paths are relative to that directory. The PDFs are the original documents; the text files contain uniformly extracted text for each page. You may render and read the PDFs directly.

Public requests and reference answers are at `/task/data/validation/queries.jsonl` and `/task/data/validation/labels.jsonl`. The remaining questions are not provided. The original corpus and public examples are read-only.

## Expected Artifacts and Interfaces

Create executable `/app/build.sh` and `/app/run.sh`, with the code and files they need under `/app`:
`/app/build.sh --corpus /task/data/corpus --index-dir /work/index` `/app/run.sh --index-dir /work/index --queries /work/input/queries.jsonl --output /work/output/answers.jsonl`

Each input JSONL row contains `query_id`, `doc_id` and `question`. Return one JSONL row for each query, with the same `query_id`, an `answer` string and a `pages` list of the supporting document's page numbers. Page numbers start at one. Give the final answer directly, including units where applicable; a list answer may be expressed as a list in the string. Use an empty `pages` list when no supporting page exists. Write diagnostics to stderr.

## Resources and Execution Permissions

The environment provides 8 CPU cores, 32 GiB RAM and 100 GiB storage, with no GPU. Development has a two-hour budget. Index construction may take up to four hours. The system must handle up to 2,500 requests in two calls of at most 1,250 requests, with an independent 10,800-second allowance per call. Completed valid JSONL rows remain usable after timeout; missing or invalid rows are unsuccessful. A command failure other than timeout invalidates that call. Honor the supplied index and output paths.

During verification, build and query commands run as a non-root user. The implementation under `/app` and the supplied inputs are read-only. The passed index directory already exists and is writable, but its parent directory is not writable. Create build files, caches and temporary directories inside that index directory or the supplied `TMPDIR`; do not create sibling directories or rename the index directory itself. The index persists and remains writable across query calls. Write results at the passed output path, whose parent directory is writable. Honor `TMPDIR` and `XDG_CACHE_HOME` rather than writing to `/app` or assuming a writable system temporary directory.

## Environment and Development Checks

Use only the external resources described in `/task/docs/available_resources.md`. Before starting, also read `/task/docs/environment.md`. Evaluation checks executable behavior, output validity and answers on held-out questions, together with the task's resource and API rules. It runs in a separate environment with the submitted `/app` files and the supplied corpus.

You may use the public examples to implement and check the complete build and query path during development. Include all required implementation files under `/app` so the system runs after a fresh start with the supplied inputs.
