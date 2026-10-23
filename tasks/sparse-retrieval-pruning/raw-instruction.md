# Sparse Retrieval Pruning

## Task Description

Optimize the supplied sparse retrieval system over a large corpus.
Each document and query is represented by a set of opaque term IDs. Given a
query, return the most relevant corpus documents while keeping total search
wall time low.

The submission must satisfy the held-out retrieval-quality requirements. Its
reward increases linearly with starter-relative throughput from 4× speedup
(zero reward) to 16× speedup (full reward); 10× earns 0.5. You may replace the starter index or
retrieval algorithm as long as the executable interface and output contract
are preserved.

## Requirements

- Create or modify submission files only under `/app`.
- Treat `/task` as read-only.
- Do not use precomputed hidden query-to-document mappings, hidden relevance
  judgments, or external datasets/services containing evaluation answers.
- Build retrieval state from the supplied corpus through `build.sh`; do not
  require undeclared persistent files from the verifier.
- `build.sh` and `run.sh` must be executable files under `/app`.
- Implement all submission logic in Python source code. `build.sh` and `run.sh`
  may be thin Bash wrappers for argument parsing and launching Python, but all
  indexing, retrieval, scoring, pruning, and ranking logic must be Python.
- Do not add or compile native submission source code, including C, C++, Rust,
  or Go, and do not have `build.sh` produce a native executable. Preinstalled
  Python packages such as NumPy may be used through their normal APIs.
- The submission build and search path must be single-process and single-threaded:
  do not use multiprocessing, worker pools, threading, joblib, Ray, or parallel
  query execution. The verifier environment is limited to one CPU, so additional
  threads cannot obtain extra aggregate CPU throughput; CPU limitation does not
  by itself authorize or make parallel execution valid.
- Read `/task/docs/environment.md` for the runtime and resource limits.
- Read `/task/docs/index_format.md` before changing the starter index. The
  documented format is an implementation detail and may be replaced.
- Read `/task/docs/available_resources.md` for the local dependency policy.
- The evaluator allows up to 120 minutes for the Agent phase.

### Build interface

The verifier invokes:

```bash
/app/build.sh \
  --corpus /task/data/corpus.jsonl \
  --index-dir /path/to/index
```

`build.sh` must create all persistent index and runtime artifacts under the
provided `--index-dir` and return status `0` only when the index is ready.
The build step may use public statistics located next to the corpus, but may
not require additional undeclared paths.

### Search interface

After a successful build, the verifier invokes:

```bash
/app/run.sh \
  --index-dir /app/index \
  --queries /path/to/queries.jsonl \
  --output /path/to/results.jsonl
```

`run.sh` must process every supplied query exactly once, preserve input query
order, and write one result object per input query. Required runtime state must
come from the supplied index directory and query file.

### Input format

Documents and queries use JSONL. A document has the form:

```json
{"doc_id":"document-id","terms":["term-id", "term-id"]}
```

A query has the form:

```json
{"query_id":"query-id","terms":["term-id", "term-id"]}
```

The terms in each row are unique opaque strings. Their lexical value, numeric
appearance, input order, and position do not encode relevance.

## Output contract

Each output line must be a JSON object with this shape:

```json
{"query_id":"query-id","results":[{"doc_id":"document-id","score":0.123}]}
```

For every valid query:

- `query_id` must identify the corresponding input query;
- results must contain at most 100 items;
- every result `doc_id` must occur in the supplied corpus;
- document IDs must be unique within a query;
- every score must be finite and numeric;
- results must be ordered by descending score; and
- equal-score results must be ordered by opaque document ID in ascending
  lexicographic order.

Returning fewer than 100 results is valid but may reduce Recall@100.

## Available validation data

The following files are available to the Agent:

- `/task/data/corpus.jsonl` — the full corpus;
- `/task/data/validation/queries.jsonl` — validation queries;
- `/task/data/validation/qrels.tsv` — validation relevance judgments;
- `/task/data/validation/stats.json` — validation term and document-frequency
  statistics;
- `/task/data/validation/reference_top100.jsonl` — validation regression rankings.

The formal hidden query split and hidden relevance judgments are verifier-owned.

## Expected artifacts

The finalized submission must contain executable `build.sh` and `run.sh` under
`/app`:

```text
/app/
├── build.sh
├── run.sh
├── src/              # optional Python modules
└── README.md         # optional notes
```

All required persistent search artifacts must be written beneath the
`--index-dir` supplied to `build.sh`.

## Unpruned reference baseline

The verifier uses the unpruned reference starter as the latency baseline. It:

- retains every corpus term and every posting;
- does not apply DF, prefix, or other posting-list pruning by default;
- uses the set-valued corpus/query input without weights;
- builds a consistent dictionary, metadata, and posting layout; and
- performs unpruned binary/IDF-overlap search.

Any optional pruning flag in starter code is for explicit local experiments
only and is not used for the verifier baseline.

## Verification and reward

The verifier rebuilds the submission from the full corpus and runs it on a
private query split. It checks retrieval integrity, executable behavior, output
validity, retrieval quality, and search wall time.

The hidden results must satisfy:

```text
NDCG@10 >= 0.89
qrels Recall@100 >= 0.99
```

The fixed corpus contains 1,000,000 documents. Each formal search invocation
processes the same 1,000 hidden queries; the public development set contains
200 queries. The verifier runs five measurement rounds with fresh processes. Odd rounds run
starter then candidate; even rounds run candidate then starter. It uses the
median of each system's five complete search wall times and divides the starter
median by the candidate median. Timing includes process launch, Python imports,
index loading, reading all queries, retrieval, output writing and process exit.
There is no separate warmup and the OS file cache is retained between calls.
Each round uses a fresh private output directory and temporary HOME/TMPDIR; the
built index and submission source are read-only during search. Do not write to
the index, reuse answers across invocations, or rely on files from earlier runs.
All required persistent state must be built from public inputs. The verifier
isolates accessible paths and clears temporary state between invocations.
Every candidate round must meet both quality floors; reported aggregate quality
is the arithmetic mean across rounds. Outputs are validated in every round.
Both positive finite timing medians are required; failures yield zero reward.

The candidate build is limited to 3,600 seconds, the reference build to 1,800
seconds, and each complete search invocation to 900 seconds. The overall
verifier budget is 16,200 seconds, covering builds, ten searches and the
integrity judge. Both systems use the same one-CPU affinity, 32 GiB memory
limit, one-thread library settings and isolation. New threads are blocked;
Python worker processes are monitored and the trajectory is audited. Thin
serial shell launch wrappers remain allowed. This protocol does not grant
permission to run additional workers.

Define `s = median starter wall time / median candidate wall time`.
If every round passes both quality gates, execution, output validation and the
trajectory judge, reward is `max(0, min(1, (s - 4) / 12))`; otherwise it is zero.
Display score is `100 × reward`. Submission-reported timings are diagnostic only.
The formal build and search run offline and must not require credentials,
remote models, package downloads or external services.
