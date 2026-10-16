I need to investigate issues in several code repositories. Before making a change, I want to find the implementation, related code and tests I should read to understand the issue. Build an executable search engine that takes an issue and its repository snapshot and returns the relevant source regions. The goal is to retrieve useful reading context; you do not need to produce a patch.

Read `/task/docs/environment.md` and `/task/docs/available_resources.md` for the runtime and permitted retrieval and generative APIs. Follow their provider, model and credential restrictions. Do not look up external repositories, issues, patches, answers or relevance labels, hard-code evaluation answers, access hidden grading data or manipulate grading. Do not put credentials into submission files or generated artifacts.

Repository snapshots are under `/task/data/repos/<snapshot_id>/`. Queries contain `query_id`, `snapshot_id` and `text`; search only the snapshot named by each query. Public development questions and reference regions are available in `/task/data/validation/queries.jsonl` and `/task/data/validation/ground_truth.jsonl`.

Put your implementation and dependencies under `/app`, and treat `/task` as read-only. You have 2 hours, 16 CPU cores, 32 GiB RAM and 100 GiB storage, with no GPU. Submit executable `/app/build.sh` and `/app/run.sh`. The verifier transfers `/app` into a fresh environment and runs your commands as an unprivileged user; global installations and running processes from development do not transfer. During verification, `/app` is read-only except for the supplied index directory.

The verifier first invokes:

```bash
/app/build.sh \
  --corpus /task/data/repos \
  --index-dir /app/index
```

Build the required artifacts in the fresh index directory and return successfully within 3,600 seconds. Any service you start must be ready before this command finishes. Keep generated runtime files in that directory; a service started during build may remain running for queries.

After the build succeeds, the query interface is:

```bash
/app/run.sh \
  --index-dir /app/index \
  --queries /path/to/queries.jsonl \
  --output /path/to/results.jsonl \
  --top-k 5
```

Process every supplied query and write one JSONL result per query to the requested output path. Evaluation sends one query per invocation, sequentially. Each invocation has 180 seconds, including startup, API calls and output writing; exceeding the deadline scores zero for that query.

Each result must have this structure, using only the fields shown:

```json
{"query_id":"query-id","regions":[{"path":"src/example.py","start":20,"end":55}]}
```

Preserve the input `query_id`. Return at most five regions covering at most 500 distinct source lines in total. Use paths relative to the requested snapshot and integer, one-based, inclusive line numbers within the file. Lines are separated by physical newlines; a final newline does not add an empty line. Overlapping ranges count once, and result order does not affect scoring. An empty list is allowed and scores zero.

Quality is measured by line F1 against the reference reading context: `2 × matched lines / (returned lines + reference lines)`, matching by file path and line number. The final score is the average across hidden queries. Missing, malformed, invalid or failed query outputs score zero for that query. A failed build or confirmed integrity violation gives zero overall.
