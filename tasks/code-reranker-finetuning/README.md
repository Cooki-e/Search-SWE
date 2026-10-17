# Code Reranker Fine-Tuning

Fine-tune the supplied `BAAI/bge-reranker-base` weights while preserving architecture, configuration and tokenizer. The fixed first stage combines local BM25 Top-200 with local `BAAI/bge-base-en-v1.5` embedding Top-200 through equal-weight RRF (`k=60`), retaining the whole deduplicated union of 200–400 candidates. Original and submitted rerankers use exactly the same lists. Reward measures mean Accuracy@5 gain normalized by fixed-candidate headroom over all 200 hidden questions.

[raw-instruction.md](raw-instruction.md) preserves the structured source, and [instruction.md](instruction.md) is the complete agent request. Only the prose instruction reaches the agent; the structured source is outside the agent Docker context and mounts.

## Inputs and environment

The corpus has 8,765 code documents and train has 5,000 records with one positive and no supplied negatives. There is no public validation split; training records may be held out locally. An editable starter samples corpus negatives, uses two-candidate cross-entropy and exports unchanged config/tokenizer bytes with safetensors. Only `/app/output/model` is transferred, and the verifier loads it offline with remote code disabled and safetensors required. Submitted scripts are not executed.

Resources are one GPU, 8 CPUs, 32 GiB RAM and 100 GiB storage; agent time is 21,600 seconds (6 hours) and verifier time is 10,800 seconds. First-stage retrieval is capped at 2,700 seconds and both-reranker evaluation at 7,200 seconds. Failures keep zero reward. Both phases use `no-network` and receive no task API keys. The frozen encoder is mounted at `/task/models/bge-base-en-v1.5` for local candidate mining and verifier inference. Its fixed preprocessing takes the first 512 characters, adds no query prefix, truncates tokens to 512, and uses float32 CLS pooling with batch size 32 and L2 normalization. No trajectory judge is added; checkpoint checks and scoring remain deterministic, so they do not by themselves prove training-data provenance compliance.

For baseline mean Accuracy@5 B, submitted mean S and candidate-hit fraction C across all hidden questions, reward is `clamp((S-B)/(C-B), 0, 1)` when C>B and zero otherwise. Every first-stage miss remains in all denominators. B and C are recalculated, not fixed to author measurements. Neural inference uses full question/document pairs, 512-token joint truncation and batch size 16, resolving equal logits by RRF order.

## Sources and structural references

Corpus and train reuse the exact hashes and named paths from the current formal `tasks/code-embedding-finetuning/assets.json`, pinned to official dataset revision `6713b1eb7474e0768e906a0151c76af92f0cfcdd`. The reranker retains its original `BAAI/bge-reranker-base` model revision `2cfc18c9415c912f9d8155881c133215df768a70`. The local embedding model is pinned to `BAAI/bge-base-en-v1.5` revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`; all eleven model/tokenizer/metadata files were downloaded and SHA-256 verified. No data/model bytes were republished. See [SOURCES.md](SOURCES.md) for provenance and usage terms. Published inputs may be reused at their original paths. The reused hidden split is runtime-isolated but visible in the repository and has a known contamination risk.

Read-only references: `tasks/code-embedding-finetuning` for GPU training, corpus provenance, fixed-backbone model delivery and offline loading; `tasks/long-document-reranking` for candidate reranking and deterministic quality scoring. This task optimizes reranker weights with local embedding plus BM25 candidates, has no public validation split, and keeps its headroom-normalized reward instead of the reference metrics.

## Historical author measurement

An earlier author-only local A100 run substituted local BGE embeddings for the API: original reranker Accuracy@5 was 1.5% (3/200), candidate ceiling 23.5% (47/200), headroom 22.0 percentage points, with 76,788 scored pairs and 350–399 candidates per query (mean 383.94). RRF before reranking scored 2.5% (5/200). The ceiling is lower than the historical embedding-only Top-500 ceiling of 28.0%. These historical results do not validate the current local inference implementation or demonstrate trained-checkpoint improvement. Retrieval parameters were not changed using those hidden scores. Historical outputs remain in author development evidence, outside the agent and public data.

## Validation

From the repository root, restore inputs with `python scripts/download_assets.py --task code-reranker-finetuning`. Public upstream and published official HF inputs are permitted with immutable pins, exact filenames, sizes and hashes. Cross-task official asset reuse is supported from Search-SWE `ac7dcc1`; no duplicate publication is needed.

Use `python scripts/check_tasks.py tasks/code-reranker-finetuning`, `python scripts/download_assets.py --task code-reranker-finetuning --verify-only`, and `python -B -m unittest discover -s tasks/code-reranker-finetuning/tests -p 'test_*.py' -q`. Launch through `scripts/run_task.sh --task code-reranker-finetuning`, which preserves real Compose GPU reservations with the documented Harbor override.

### Current 6-hour evaluation

The October 17 trial evaluated **v0.3.1 with the current 6-hour budget**, using Codex 0.157.1 + OpenRouter `openai/gpt-6-luna`, effort `max`, on one A100 40GB. It completed normally, without agent timeout, trial errors or retries. Agent execution took **10,901.70 seconds (3 hours 2 minutes)** and separate verification **1,398.98 seconds (23 minutes 19 seconds)**.

On all 200 hidden questions, baseline Accuracy@5 was **0.015 (3/200)**, submitted Accuracy@5 **0.09 (18/200)**, candidate ceiling **0.235 (47/200)**, and final reward **0.3409090909**. The checkpoint loaded offline and passed the fixed-backbone/tokenizer checks. The task has no semantic or trajectory judge. The model reported 56.6% Accuracy@5 on its own 500-query training holdout; that local measure is separate from the hidden result above. No task constraints or scoring were changed in response to the result.

The run used the README's `bash scripts/run_task.sh` entry directly in the right-hand Herdr pane. Results are in `jobs/code-reranker-finetuning-codex-openrouter-luna-max-20261017-6h-attempt3/2026-10-17__01-32-07/`; author records are in `contributing/dev/code-reranker-finetuning/2026-10-17-6h/`. The evaluated instruction SHA-256 is `d62f93219ce821e2ebe23510f5983e984af7ff567cc74cec6649fda7868a9e81`. Both temporary GPU UUID bindings were restored to portable one-GPU reservations after completion, and the GPU 3 reservation was released. All other runtime files match the prelaunch review snapshot.

On October 17, against `ac7dcc1`, merge-ready and release checks, all 19 asset hashes, 25 task tests and the 174-test shared suite passed. The 5,000 training queries and 200 hidden query texts have no exact overlap. The earlier offline encoder smoke check also passed. The consolidated author review is `contributing/dev/contribution-readiness/2026-10-17/REVIEW.md`.

### Earlier 12-hour evaluation

The October 15–16 trial used v0.3.0 with a 12-hour budget. It took 33,677.75 seconds in the agent phase and scored **0.2954545455** (submitted Accuracy@5 **0.08**). Its job is `jobs/evaluations/code-reranker-finetuning/codex/openai/gpt-6-luna/max/attempt-1/2026-10-15__14-05-36/`. A mistakenly started duplicate attempt 2 was cancelled. These records remain historical; the completed 6-hour trial above is the evidence for the current version.
