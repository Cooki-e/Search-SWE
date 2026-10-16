# Code context retrieval

## Objective and inputs

Implement a reusable search engine that locates source regions needed to understand and address an issue in its supplied repository snapshot. Retrieve reading context; generating a patch is not required. The objective is high line F1 on held-out issues.

- Corpus: `/task/data/repos/<snapshot_id>/`, one directory per snapshot.
- Public development inputs: `/task/data/validation/queries.jsonl` and `/task/data/validation/ground_truth.jsonl`.
- Queries contain `query_id`, `snapshot_id` and `text`. Only files in that snapshot are eligible.
- Read `/task/docs/environment.md` and `/task/docs/available_resources.md`. Only the documented retrieval and generative APIs are permitted. No external repository, issue, patch, answer or label lookup; no hard-coded evaluation mappings, hidden-file access or grading manipulation. Credentials must not be included in submitted files or artifacts.

## Runtime and submission

- 16 CPU cores, 32 GiB RAM, 100 GiB storage, no GPU; development budget 2 hours.
- Put implementation and dependencies under `/app`; `/task` is read-only. The entire `/app` transfers to a fresh verifier. Agent-installed global dependencies and running processes do not transfer.
- Submit executable `/app/build.sh` and `/app/run.sh`.
- In the verifier, commands run unprivileged, `/app` is read-only except the provided index directory, and query output must be written to the supplied output path.
- Build once, within 3,600 seconds, including any service startup:

```bash
/app/build.sh --corpus /task/data/repos --index-dir /app/index
```

- The verifier supplies a fresh index directory and requires successful build exit. Keep generated runtime files there. Services started during build may remain running; build must return when ready.
- Query invocation:

```bash
/app/run.sh --index-dir /app/index --queries /path/to/queries.jsonl --output /path/to/results.jsonl --top-k 5
```

- Process all input queries and produce exactly one JSONL result per query. Private evaluation invokes one query at a time, with concurrency 1. Each invocation has 180 seconds including startup, API calls and output writing.

## Output and quality

A result has exactly `query_id` and `regions`; each region has exactly `path`, `start`, `end`:

```json
{"query_id":"query-id","regions":[{"path":"src/example.py","start":20,"end":55}]}
```

Preserve the input query ID. Return zero to five regions and at most 500 distinct source lines in total. Paths are repository-relative; line numbers are integers, one-based and inclusive, within actual file bounds. Physical newlines delimit lines; a final newline does not add an empty line. Overlapping ranges count once; ordering does not affect quality. An empty region list scores zero.

Single-query quality is line F1: `2 * matched_lines / (returned_lines + reference_lines)`, where lines match by file path and line number within the query's snapshot. The final quality score is the mean on hidden queries. Missing, malformed, invalid, failed or timed-out query outputs score zero for that query. Build failure or confirmed integrity violation scores zero overall.
