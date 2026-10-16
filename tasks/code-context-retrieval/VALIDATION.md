# Local validation, version 0.1.0

The current package uses real source directories under `data/repos/<snapshot_id>/`. It has passed local grader and corpus-based retrieval checks. It remains unpublished, and a full coding-agent trial has not been run.

Instruction SHA-256: `086f401e40a692ae75c76ab35dc8d4456e62c28e27590a38b325ad90f3c38489`. Structured source SHA-256: `66ca51504312e7443c8d2eb58d82cce07e4493afaf8b58514f3811dd7e6dcba6`. Grader SHA-256: `c3252d804b9ccf47c3e24a470baa35fe523989ad78156a64ff3514c9add213ca`. Scorer SHA-256: `2db20cec9e79fc0c54a7d9cccbf6edde40184f7e97c72c59baf8992736739823`. The full package inventory is in `task_development/code-bug-localization/package-build/package-hashes.json`.

## Checks on the current directory layout

- Compared all 51,920 files against both the previous JSONL and the pinned file inventory: all 324,317,309 source bytes and all physical line counts are unchanged. All 30 original issue texts and gold region sets are unchanged. Every reference output remains legal and scores one.
- Confirmed 30 anonymous snapshot root names, each query's explicit snapshot scope, and disjoint validation/test snapshots. Internal file paths, source contents and issue text are preserved; this does not claim that project identities cannot be inferred from those contents.
- Verified all 51,922 public asset files, including the two validation files, against their sizes and SHA-256 hashes. Local staged release validation with `allow_unpublished=True` passes. The checker was run with process-local `core.quotepath=false` so six original Unicode filenames are compared correctly; no Git configuration or filenames were changed.
- Parsed both Compose overlays and checked every mounted source. The agent container exposed the repository directories, ten validation questions and docs as read-only. Hidden labels, the author-side source mapping and GPUs were absent.
- Ran eight scorer regression tests, including physical newlines, identical paths in different snapshots and rejection of source symlinks. The source line matching and F1 formula are unchanged.
- Built `search-swe-local:code-context-retrieval-verifier-repos-v010` from the standard CPU image. The unchanged agent image was reused for the mount checks. Ran the following author-only fixtures in fresh containers with network disabled, 16 CPU cores, 32 GiB RAM, no GPU and submission UID 10001 through the real build/run interface.

| Author-only fixture | Expected reward | Observed reward |
| --- | ---: | ---: |
| Complete-gold oracle | 1.0 | 1.0 |
| Malformed/invalid outputs and isolation probes | 0.0 | 0.0 |
| BM25 indexing and retrieval from `repos/` | 0.1050217889 | 0.1050217889 |

The directory-based BM25 fixture built in 106.55 seconds; its slowest query invocation took 0.37 seconds. Its score exactly matches the previous corpus-based pilot. It has no hidden labels. The oracle and invalid-output fixtures deliberately contain author-side reference material and validate the grader; they are not legitimate search implementations or coding-agent trials. No fixture is supplied in the task.

The negative fixture processes all 20 questions and checks malformed JSON, duplicate fields, nonfinite numbers, invalid Unicode, unknown paths, bad bounds, wrong IDs, excess regions/lines, process errors, symlinks and FIFOs. Its permission probe confirms that submitted code cannot read hidden labels or the grader, rewrite rewards/reports or submitted code, or write source files in the mounted `repos/` tree.

## Retained earlier evidence

The previous package and evidence are retained under `package-build/before-repos-layout/`. Earlier checks covered build failure, a real 180-second timeout with the remaining 19 questions scored, 2,970 pilot metric comparisons, and repository integration tests. The timeout/supervision and F1 calculation are unchanged; those checks were not repeated for this input-layout change. The current layout was separately validated with the oracle, negatives and actual BM25 retrieval above.

Structural precedents remain `tasks/reasoning-query-rewriting` and `tasks/agentic-search` at base `46197a43f8cbb364e72b6d63d5db873ae7d2cac8`. The standard CPU/API docs and policy are unchanged. User-requested CLI examples are retained. Development remains 7,200 seconds, build 3,600 seconds and each query 180 seconds.

## Remaining layers

No full coding-agent trial, live OpenRouter/Jina measurement, upload, image publication, commit or PR was performed. The earlier local Qwen screening does not establish coding-agent performance or API latency in the final CPU environment. Strict release validation reports only the unpublished asset pins; their revisions remain `null` pending publication. No remote reproducibility or release-ready status is claimed.

Author-side evidence: `task_development/code-bug-localization/package-build/repos-layout-verification.json`, `repos-static-check.json`, `repos-staged-release-check.json`, `repos-agent-environment-check.json`, `repos-runtime-summary.json` and `runtime/repos-*/`.
