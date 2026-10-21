# Local validation

Task version: 0.3.0. Author: Bingyu. This records local execution evidence and
the subsequent official asset pins. It is not a configured coding-agent trial.

## Reviewed structure and artifacts

Reviewed `tasks/query-encoder-alignment` at repository base
`46197a43f8cbb364e72b6d63d5db873ae7d2cac8`, plus the local
`methodology-inspiration-retrieval` and `decision-model-training` packages.
Reuse covers the shared GPU image, separate verifier and mount/protection
patterns. This task instead measures complete batch retrieval time after a
quality gate, allows corpus indexing, and supplies no reference implementation.
The user's requested fenced command examples are retained; the complete
raw-to-rewritten correspondence is in `instruction-audit.json`.

Only this task and the required GPU/network-policy inventory entries were added.
Source data, preparation scripts, trained checkpoints, indexes and measurements
are in `../../../task_development/lightretriever`, outside the solver package.

## Inputs and legal feasibility witness

The exact 80,000-example sample covers all 23 original sources. The original
query/positive/negative texts are preserved. One normalized exact test-query
overlap was replaced from its own source; zero remain. Sampling provenance,
source revisions, sizes and checksums are recorded in `sampling-report.json`,
`examples-audit.json` and `final-sample-provenance.jsonl` in the authoring folder.
All nine supplied model files match the pinned original Meta Git/LFS objects;
see `model-integrity.json`. The author-trained LightRetriever adapter is absent
from all solver and verifier mounts.

The final witness uses `checkpoint-500`, trained on 62,907 distinct
examples from the supplied sample, from the original Llama-3.2-1B base.
The checkpoint's training loop took 2963.26 seconds on
one A100 40GB with 16 CPUs and a 32 GiB container limit. The input-membership
and adapter checksums are recorded in `calibration/checkpoint-500-input-audit.json`.
This is a feasibility run with a reduced dataset, not reproduction of the
authors' full training experiment.

A complete one-pass run over all 80,000 supplied examples also finished on one
A100: 3,773.43 seconds for the training loop, 3,857.96 seconds including
preparation, 20.40 GiB peak PyTorch CUDA allocation and 4.03 GiB peak host RSS.
See `calibration/trained-witness/report.json` and `full-training-input-audit.json`.
The final scored artifact deliberately uses the already-calibrated checkpoint
listed above; the later full-epoch checkpoint is not substituted into these scores.

The complete corpus index was constructed inside the task GPU image under the
same one-GPU/CPU/RAM limits. Its construction log is
`calibration/checkpoint-500-build.log`. The witness transfers that independently
built index as an artifact and copies it during the verifier build phase;
the copy time in the verifier report is not claimed as corpus encoding time.
Training, preprocessing and original index construction fit the six-hour
development budget. Retrieval variants were checked against a separate, frozen
300-query author development set. The original hidden workload was used for
task calibration, not as training data. Model training did not use hidden
questions or relevance judgments.

## Complete workload measurements

| Implementation | Minimum macro nDCG@10 | Median seconds, 1,271 queries |
| --- | ---: | ---: |
| checkpoint-250 / bm25 | 0.421111 | 0.512044 |
| checkpoint-250 / full | 0.473451 | 0.959254 |
| checkpoint-250 / lookup-bm25 | 0.442673 | 0.650280 |
| checkpoint-250 / routed | 0.456275 | 0.840109 |
| checkpoint-500 / full | 0.495216 | 0.897636 |
| checkpoint-500 / lookup-bm25 | 0.454410 | 0.452994 |
| Final configured witness | 0.454410 | 0.860873 |

Comparable formal measurements used GPU 1, an NVIDIA A100-SXM4-40GB, with
`--cpus 16 --memory 32g --network none`. Each row uses three fresh services,
24 public-example warm-up queries, shuffled hidden requests with fresh IDs,
and the complete original 1,271-query test workload. Reported quality is the
minimum of the three macro values; time is their median. Timing includes pipe
transfer, query processing, search, ranking, response transfer and JSON decoding.
The final row uses the actual frozen gate and time anchors; earlier calibration
rows used neutral bounds solely to collect measurements, so their provisional
reward fields are not task scores.

Full per-run times are retained. Some earlier CPU-heavy variants had a single
large timing outlier; these are not deleted. The specified three-run median
handles one outlier. Final evidence: `witness-runs/lookup-500-anonymous/result.json`
and its `logs/` directory. The run completed validly and passed the quality gate;
observed reward is **0.000000**.

## Current scoring and collection identifiers

The scoring rule introduced in version 0.2.0 uses a quality gate of 0.45 and
`max(0, 1 - T / 0.8)`; version 0.3.0 retains it.
One is a theoretical zero-runtime upper bound, with no positive-time full-credit
interval. Original measurements and their original rewards remain archived under
their original scoring rules. For example, the prior witness's measured
0.4581157081 seconds and quality 0.4544096731 rescore to 0.4273553649.
This is an arithmetic replay, distinct from the new final run above.

Runtime collection labels are now `corpus1`, `corpus2` and `corpus3`. A bijective
renaming is applied to the corpus, hidden queries, qrels and warm-up records.
Per-collection candidate scopes, text, IDs and relevance grades are unchanged.
The 80,000-example file has no collection field and remains byte-identical.
The full row comparison and updated checksums are recorded in
`collection-aliases-0.3.0/data-audit.json`.

Contract tests and the complete separate-verifier witness were rerun with the
anonymous collection labels. The data manifest and local staging were refreshed.
Existing image, numerical-metric and isolation evidence below is retained for
the unchanged runtime, scoring logic and protection boundaries.

The anonymous-label rerun retained exactly the same retrieval quality as the
previous run. Its observed timing is retained even when it earns zero under
the strict speed rule; label renaming is not a timing improvement. No timing
result was discarded or replaced to obtain a positive score.

The subsequent instruction-only edit removes the domain enumeration, explicit
score formula and theoretical zero-time explanation. It retains the quality
gate, zero-score time anchor and all execution requirements. Grader and input
bytes are unchanged; no new GPU run was needed for this wording edit.

## Other executed validation

- Eleven mounted asset files passed size and SHA-256 verification.
- Both Compose overlays parsed; agent and verifier images built successfully.
- The actual agent image completed CUDA forward, backward, optimizer and adapter-save checks.
- Twelve scoring/contract unit tests and fifteen disposable-container protocol,
  failure and isolation fixtures passed. Fixtures that know gold are only grader
  tests and are not used as the legal retrieval feasibility witness.
- Graded nDCG matched `pytrec_eval` on 300 questions within 2.23e-16.
- Targeted shared-image and network-policy integration tests passed.
- Local release inspection with staged unpublished data has no errors and one
  explicit publication warning. At that local validation stage, `check_tasks.py` rejected the two
  unpublished derivative data revisions. The publication update below supersedes
  that asset-pinning limitation.
- Launcher dry-run configuration was checked. No paid model call was made.

Logs and receipts are retained in the authoring folder. The complete repository
unit-suite attempt was interrupted while waiting for an asyncio executor to
shut down; it is not claimed as a successful full-suite run. No unrelated
repository code was changed to bypass that condition.

## Unrun layers and release state

No complete configured coding-agent trial was executed, consistent with the
user's earlier preference to deliver the package without an extra paid trial.
The authoring skill treats that as a separate release-validation layer; the
legal witness and fixture tests do not replace it. There is no model-trial
feedback to claim. The original local checks preceded publication. Both derived
assets are now pinned to official dataset revision
`ff16485accd6d258610c158fce45e36b50a47c3f`; their official sizes and SHA-256
hashes match the locally validated inputs. Original model pins are unchanged.

The original local package is identified by `final-package-fingerprint.json`
in the authoring folder, including each package text/private-evaluation-file hash.
The final witness's copied grader and scoring files must match those fingerprints.

## Publication verification (2026-10-21)

The two official public data files were restored into a fresh external output
directory and cache with the repository downloader. Both size/SHA-256 checks
passed: 2 files, 2.19 GiB. The original model revision and all model hashes are
unchanged. A local verification of both new packages also passed all 14 asset
checks, 9.35 GiB including the original model and paper database.

The current package passes `check_tasks.py tasks/lightweight-query-retrieval
--merge-ready --base 11a170be17a648511233e69a8ce1a9ae756aa0d9`.
Its 12 contract tests passed again. On that latest main base, shared-image,
network-policy and RewardKit-configuration checks ran 20 tests: 18 passed and
2 skipped because the host does not have harbor-rewardkit 0.2.0 installed.
No shared repository file needed an edit: current tests discover tasks
automatically. These publication changes affect paths, pins and author-facing
records; input hashes, instruction, runtime and scoring are unchanged, so the
existing GPU feasibility evidence remains applicable. No new paid model or
GPU trial was run.
