# Validation

## Official publication — 2026-10-18

The current package supersedes the historical unpublished status recorded below.
Public inputs were published as Cooki-e in [HF discussion #4](https://huggingface.co/datasets/search-swe/Search-SWE/discussions/4)
and merged into `search-swe/Search-SWE` at immutable revision
`2182510dda66f946a153a5b09515f82fb4da125e`. All 8 public input files
were freshly downloaded from that revision into a new output/cache directory;
both the repository downloader and an independent size/SHA-256 check passed.
`assets.json` now pins the official files. Input bytes are unchanged.

The 14 task regression tests passed in the existing CPU verifier image,
with current tests mounted read-only, no network and no GPU.
Across the final two-task publication checkout, the repository suite ran
174 tests: 172 passed and two optional-dependency tests were skipped. The five
scaffolding and 12 maintainer-helper tests also passed. Task-specific and
repository-wide `check_tasks.py --merge-ready --base` checks each reported zero
errors; `check_release.py` reported zero errors and zero warnings. The base
commit was `dab2e1e04904ff2731bf81849c65c639631c9499`.

The publication contains only the two task directories. Original instructions,
scoring, resource limits and model source records are unchanged. No new paid
coding-agent trial, live trajectory audit or GPU experiment was run; the
historical runtime results and their limitations below remain applicable.
Author-side publication logs are retained outside the package in
`pr_preparation/filtered-ann-methodology-20261018T061022Z/`.

## Output-contract simplification — 2026-10-18

Task version **0.10.0**, instruction SHA-256
`8d827124973298a1e1efb3268ed7ae3fa2724c53fcdbde723696e5ac5d8678fc`.

- Removed the unused corpus config and its asset-manifest entry. All eight
  remaining assets passed SHA-256 verification; corpus, queries and labels are unchanged.
- Kept the binary-format schema, removed loading code and implementation advice,
  and reviewed the rewritten instruction against the updated structured source.
- Results now require ranked document IDs only. Removed checks on submitted
  distances and their 0.001 error tolerance. Exact squared-L2 ranking, filters,
  result counts, ties, determinism, persistence and latency gates are unchanged.
- Rebuilt the verifier image. All **14 grader regression tests passed**, including
  correct ID-only output, reversed rankings, false reported distances, wrong
  neighbors, timeout isolation, replay checks and the fail-closed audit gate.
- Real subprocess permission/network checks passed. An ID-only service with three
  failed requests scored **0.7**, with all other requests continuing correctly.
- All **20 public/hidden gold ID-only responses** passed validation against the
  original corpus. This checks output acceptance, not retrieval speed or difficulty.
- Static task and selected-package release checks: **0 errors**. No paid API calls
  or GPU use. No new coding-model trial or live trajectory audit was run.

The first small validation container hit its 128-process limit when OpenBLAS
attempted to create 128 threads before tests started. Re-running with
`OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=2` passed. Task resource limits and
submission-process configuration were not changed.

Reports and before/after snapshots are under
`task_development/filtered-ann-retrieval/contract-simplification-20261018/`.
The full index build and latency run below belongs to version 0.9.0; it was not
repeated for this output-only checker change. The build/service orchestration,
input data, exact-neighbor calculation and 15 ms deadline code are unchanged.

## Migration validation — 2026-10-16

Task version: **0.9.0**. Instruction SHA-256:
`34d785fe4ed141b82fcc3acd30490ca87d3f156ce226a485b558869fb0535b0b`.

### Executed checks

| Check | Result |
| --- | --- |
| Task static checker | 0 errors |
| Selected-package release checker | 0 errors, 0 warnings |
| Published asset verification | 9/9 valid sizes and SHA-256; 2.67 GiB total |
| Source equivalence | Corpus/labels unchanged; main grader differs only in its work-directory name |
| Public/private split | 10 + 10 distinct queries; 4 single-, 4 double-, 2 triple-tag filters per split |
| Repository image/network/audit integration | 14 tests, 12 passed and 2 dependency-dependent tests skipped |
| Task grader regression tests in verifier image | 13 passed |
| Real subprocess isolation/negative checks | Passed: UID, hidden-label/reward permissions, credential filtering, IPv4/IPv6 block, exit/missing/malformed output and timeouts |
| Real partial-credit/recovery test | Three failed queries produce 0.7; remaining queries continue; 20 total requests |
| Agent and verifier Docker builds | Passed using current CPU base and repository CLI/audit pins |
| Both Compose overlays | Valid with all source paths present |
| Agent container smoke check | Public inputs available, /app empty, /tests absent |
| Shell/Python syntax and git diff whitespace | Passed |

### Full-corpus reference run

The source author's existing implementation was installed into `/app` in a fresh
verifier container. The reference stayed outside this task. The container used
8 CPUs pinned to CPU cores 0–7, 16 GiB RAM, no GPU, no network and no API keys.
This CPU affinity does not allocate GPUs.

- Fresh build: **195.972 seconds**, below the 600-second limit.
- Faiss index: `IndexIVFScalarQuantizer`, 10,000,000 vectors, 192 dimensions.
- Hidden queries: **10/10 passed**, including all 20 initial/reloaded requests.
- Maximum request latency: **7.239 ms**, below 15 ms.
- Service loads: 2.032 and 2.066 seconds, outside query timing.
- Raw retrieval score: **1.0**.
- Live trajectory audit: **not run**. No model API charges were incurred.
- Final reward: **0.0**, and `test.sh` exited 1 because the required audit had no
  credentials. This confirms the missing-audit gate; it is not a retrieval failure.

Detailed logs, original files, query provenance, file hashes and command records
are under `task_development/filtered-ann-retrieval/migration/` outside the task.
The reference result is in
`reference-full/filtered-ann-retrieval-eval/evaluation.json`.

### Limits of this validation

No configured coding-agent trial or live model audit was run; the user previously
prohibited additional paid API usage. Thus this is a validated migration with a
known-good retrieval run, not a new coding-model difficulty measurement or a
complete audited Harbor trial. The original retrieval thresholds were retained.

The unrestricted repository release checker reports existing unpublished inputs
and ignore-check issues in other unfinished tasks. The selected-package check
for this task has no errors. Official asset publication, final redistribution
review and remote PR name checks were not requested or performed; immutable
personal HF references were preserved. No commit, push or publication occurred.
