# Validation record

This submission is supported by full author-implementation runs and a completed
Harbor Oracle trial. No independent configured coding-model trial has been run;
review of that validation coverage is requested. Nothing here should be
interpreted as an API-model score. Official asset pins are still needed before
the task can pass the merge-ready check.

The contribution branch is `add-rust-bm25-search`, based on
`46197a43f8cbb364e72b6d63d5db873ae7d2cac8`. The contributor is
MXueguang (`x93ma@edu.uwaterloo.ca`). A design summary was recorded before scaffolding
in ignored `jobs/rust-bm25-search-authoring/design-before-scaffold.json`.

## Full reference

The pinned corpus passed SHA-256 verification and a full count/unique-ID audit.
All 8,841,823 IDs are present. Dev contains 6,980 queries; the 54 public DL20
warmup queries have no ID or normalized-text overlap with dev. All dev queries
have positive judgments. Only passage text was indexed.

Pyserini 1.4.0 with k1=0.9, b=0.4 achieved MRR@10
`3236243/17589600 = 0.18398616227770956`. On this host under a 4-CPU, 16-GiB
container limit, indexing took 88.891 seconds and produced 660,057,576 bytes.
The full warm dev batch took 28.029 seconds (249.029 sequential queries/s).
Five new-process startup samples had median 6.175 seconds; they include
Python/JVM and optional-module import overhead, and do not evict OS file cache.
Sampled peak process RSS was 1,379,392 KiB. These are observations, not stable
machine-independent latency or memory guarantees.

Initial reference import failed because a Pyserini optional module constructed
an OpenAI client without a key. A documented non-secret constructor sentinel
fixed that local-only import; no service was contacted. The fresh retry then
completed all queries. Full metadata is in `reference-observation.json`.

## Local checks

Metric/protocol tests cover exact quality comparison, full query denominator,
multiple relevant hits, rank 10, malformed/duplicate/nonfinite output,
timeouts, process cleanup, overlap, cold/warm inconsistency and index links.
Both Docker contexts build with pinned Rust and an offline dependency lock.
The container isolation probe checks that submitted code cannot read hidden
qrels, change rewards, read raw corpus or an outside cache during search,
truncate the immutable index, or create a persistent cache during search.

The probe exposed a missing execute grant for the ELF interpreter; that was
fixed explicitly and both index/search probes now pass. Landlock ABI 1 is
available on this host. Compilation uses Unix privilege separation rather
than Landlock, since ABI 1 forbids the cross-directory renames Rustc needs.
Search uses both root-owned read-only artifacts and Landlock confinement.

## Commands and outcomes

- `python -m unittest discover -s tasks/rust-bm25-search/authoring -p 'test_*.py'`:
  17 tests passed. Added regressions include a full stdin pipe, a descendant
  retaining stdout, huge numeric output, and a compiler temporary file that
  disappears while workspace usage is measured. A non-table Cargo `package`
  value is also rejected as an invalid submission rather than an infrastructure
  error; that case passed in a fresh final-image container with reward zero.
- `.venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py'`:
  171 discovered, 169 passed, 2 skipped because host `harbor-rewardkit==0.2.0`
  is absent. Those two tests concern other tasks' model-judge backend; this
  task has no judge dependency. No failing test was disabled.
- `.venv/bin/python scripts/check_tasks.py tasks/rust-bm25-search`: zero errors.
  `.venv/bin/python scripts/check_release.py`: zero errors and warnings.
- Asset downloader `--verify-only`: both files verified against pinned hashes.
  Both Compose overlays rendered against a temporary base service; shell
  syntax, Python compilation and `git diff --check` passed.
- Both Docker images built using `sudo -n docker` on this host. Agent CLI
  versions were checked inside the final image: Rust 1.85.1, Codex 0.157.1,
  Pi 0.87.1, Claude Code 2.1.283. The agent image contained no verifier qrels,
  reference worker or hidden dev queries. The public synthetic test passed
  with the privately authored Rust binary.
- `authoring/check_negative_containers.py --sudo --output .../negative-final`:
  missing source, a failing index command and malformed search output each
  produced `invalid_submission` with reward 0 in a new separate container.
  Timeout and process-cleanup cases were exercised by the protocol tests.
- `authoring/check_isolation.py` inside a disposable verifier: passed indexing
  and search access checks, including unchanged reward and denied hidden data,
  raw-corpus search access, outside cache reads, index truncation and cache writes.
- Merge-ready checker with base `46197a43f8cbb364e72b6d63d5db873ae7d2cac8`:
  four expected errors, requiring both data entries to use the official
  `search-swe/Search-SWE` repository and `tasks/rust-bm25-search/` prefix.
  Development pins remain real immutable Tevatron commits; no official SHA
  has been fabricated to hide the publication prerequisite.

Repository integration required adding the new offline task to the explicit
network inventory, documenting that it requires no trajectory-judge credential,
and installing the repository's pinned agent CLIs. The first repository test
run caught those omissions; the rerun passed with the complete integration.

The first full author trial built the entire Rust index but failed at startup
because of the verifier's missing ELF-interpreter grant. Its zero was an
infrastructure defect, not a retrieval-quality failure. After that fix, the
next full trial passed with MRR `0.18729482194023742`, score `0.377625401141`,
696,567,340 index bytes, 310.285 seconds to build, 112.697 seconds for dev,
61.936 sequential queries/s, cold median 0.429 seconds and peak process RSS
793,632 KiB. Its fresh local reference reproduced the exact pinned MRR.
The score below 0.5 is expected: this simple self-built implementation is
slower on warm queries despite meeting the quality floor.

The final repeat uses the hardened request/EOF controller. A later workspace
monitor fix only tolerates compiler temporary files disappearing during its
directory walk; the specific regression and a fresh compile/command-failure
container passed. It changes neither retrieval, measurement nor scoring.
The full repeat's image fingerprint and any post-run source difference are
recorded separately from the final image; model evaluation remains unperformed.

The repeat completed successfully: MRR `0.18729482194023742`, reward
`0.376796488284`, 696,567,340 index bytes, 308.297 seconds to build, 112.046
seconds for the full dev batch (62.296 sequential queries/s), cold median
0.431 seconds and sampled peak search-process RSS 790,120 KiB. Its entire
6,980-response file has the same SHA-256 as the preceding full run:
`c8483498457948202f20419ac78dd9fb18933a741803efc94c66cc00ef06baab`.
The two warm batch times differed by about 0.58%. This is limited evidence
from one host, not a cross-machine reliability study.

[known-good-observation.json](known-good-observation.json) includes the full
metrics, same-run reference, source/image hashes and the narrowly scoped
post-run monitor fix. The evaluated instruction SHA-256 is
`9f566cfdd7465d093da2c619a0d2ad6936ad39dcdbad0a630193b52328de8b62`;
the author trial tests its interface with prepared source, not a model reading
that instruction. Full local logs remain in ignored
`jobs/rust-bm25-search-authoring/author-final-03` and negative-case directories.
The author Rust source/index are also ignored and are not in the agent image
or a public solution directory. Completed author containers were removed after
preserving their relevant artifacts and logs.

## Validation scope and merge follow-up

The contribution is submitted with the completed author and Oracle evidence.
An exception to the workflow's independent coding-model trial is requested for
maintainer review. No model trajectory, model score or model-driven task feedback
is claimed. Input redistribution review, official dataset publication and
immutable official HF pins remain outstanding before merge-ready validation.

`.venv/bin/python scripts/run_task.py --task rust-bm25-search --dry-run`
stopped with `Set --model or AGENT_MODEL`. This confirms the missing model
configuration; it is not a completed trial or a model failure. The manual author
trials supplied only the source artifact to a separate verifier. A subsequent
Harbor Oracle integration trial checks the actual artifact path using the same
private author source; its record below is separate from model evaluation.

No paid trial was launched or substituted. This task's deterministic verifier
needs no judge key. A future independently configured model trial, if requested
during review, should follow the repository's evaluation guide and use a fresh
output directory.

## Harbor integration follow-up

An ignored private task snapshot under
`jobs/rust-bm25-search-authoring/harbor-integration/rust-bm25-search` adds an
Oracle `solution/` containing only the existing author source. No solution was
added to the public package or agent image. Harbor 0.22.0 compiled that source
offline, passed the public synthetic check, and collected exactly `Cargo.toml`,
`Cargo.lock` and `src/main.rs`; all three collected files match their input hashes.

The first integration attempt stopped before starting a task container because
the local sudo Docker wrapper discarded Compose infrastructure variables. The
job-scoped wrapper now preserves only those named non-secret variables; no host
Docker permissions or network settings were changed. The second attempt found
an actual task integration defect: Docker rejects explicit `hostname` and
`extra_hosts` when Harbor shares its egress-control sidecar's network namespace.
Those Compose options were removed. The verifier startup now ensures its
inherited hostname has a local `/etc/hosts` entry when needed. Prompt, quality
floor, scoring and resource limits are unchanged.

The third integration attempt completed successfully: one total/completed trial,
zero errored/running/pending trials, no trial exception, verifier status `ok`,
quality gate passed, and Harbor reward `0.379283503451`. Docker inspection
confirmed 4 CPUs, 17,179,869,184 bytes of memory and memory-plus-swap, 256 PIDs,
and Harbor's separate restricted network namespace. Its runtime source snapshot
and initial failed-attempt diagnoses are retained in the ignored run directory.
This is an Oracle integration check, not the required configured coding-model
trial.

The exact launch arguments, with the checkout-relative executable and paths,
were:

```bash
.venv/bin/harbor run \
  --path jobs/rust-bm25-search-authoring/harbor-integration/rust-bm25-search \
  --agent oracle --env docker --force-build --yes \
  --n-concurrent 1 --n-attempts 1 --max-retries 0 --job-name oracle-03 \
  --jobs-dir jobs/rust-bm25-search-authoring/harbor-integration/runs
```

The process used the job-local sudo Docker wrapper described above. Use a fresh
job name when reproducing. The author source is private and is not restored by
downloading the public task assets.

Candidate MRR is again `0.18729482194023742`; all 6,980 responses match both
previous manual runs byte-for-byte. Compilation took 19.272 seconds, indexing
307.627 seconds, and the index contains 696,567,340 logical bytes. Warm search
took 111.092 seconds (62.831 sequential queries/s), cold median was 0.439 seconds,
and sampled peak search-process RSS was 790,820 KiB. The same-run reference
reproduced exact MRR `3236243/17589600`, took 26.271 seconds for warm search and
occupied 660,157,062 bytes. Complete measurements, terminal state, image/source
hashes and artifact fidelity are in [harbor-observation.json](harbor-observation.json).

During that run, a separate malformed-manifest probe exposed an `AttributeError`
for `package = []`. The final grader checks the table type explicitly. The new
regression covers arrays, strings, booleans and integers, and
`check_negative_containers.py --sudo --case malformed-manifest` passed in a fresh
container. The only runtime-source difference from the full Harbor snapshot is
this rejection guard; valid candidate execution and measurement are unchanged.

An anonymous read-only publication preflight downloaded only official metadata
at `6713b1eb7474e0768e906a0151c76af92f0cfcdd` and found no collision with the two
proposed task paths among 335 existing asset records. That existing SHA does not
contain this task's assets and is not used as their source pin. No upload was
made. The upstream terms were checked and recorded in [SOURCES.md](SOURCES.md);
maintainer review and publication remain outstanding.
