# Agentic Search — Vectorless

Build retrieval over the 100,195-document BrowseComp-Plus corpus without embeddings, BM25 or external retrieval/reranking. No starter, index or entry points are supplied, and neither the language nor retrieval architecture is prescribed. Each query may make at most 20 independent retrieval rounds. Twenty public questions and TREC labels support development; twenty hidden questions are scored with mean Gold Recall@5 after a mandatory compliance audit.

[raw-instruction.md](raw-instruction.md) is the structured specification. [instruction.md](instruction.md) is the complete prose request sent to the agent. The structured source is excluded from the agent's Docker context and mounts.

## Environment and verifier

The CPU shared image provides 32 CPUs, 128 GiB RAM and 200 GiB storage. Agent time is 7,200 seconds. The verifier discards the transferred `/app/index`, builds once as UID/GID 65534 and runs up to five query invocations sharing the fresh index and any optional build-started service. Build has a 600-second cap. Build, query execution and deterministic scoring share a 15,300-second wall-clock allowance, with no individual query timeout. The verifier has 19,200 seconds including a separate audit of up to 3,600 seconds. Any execution/output failure invalidates the entire submission.

Submitted processes receive an explicit environment allowlist and the task `OPENROUTER_API_KEY`, never judge credentials. The task-local `tests/trajectory_gate.py` orchestrates retrieval and the mandatory audit. After retrieval, submission processes stop before auditing. The judge uses RewardKit 0.2.0, LiteLLM 1.97.0 and Codex 0.147.0 with `deepseek/deepseek-v4.1-flash` at `https://openrouter.ai/api/v1`. Configure host `VERIFIER_OPENAI_BASE_URL` and `VERIFIER_OPENAI_API_KEY` locally; the latter is a separate OpenRouter judge key. Missing trajectory, bad output, judge failure/timeout or a detected violation leaves zero reward. Algorithm and round-limit auditing is not a formal guarantee of detecting every violation.

## Sources and structural references

The corpus/public split has the exact current `tasks/agentic-search/assets.json` hashes and named paths, pinned to official dataset revision `6713b1eb7474e0768e906a0151c76af92f0cfcdd`. No source bytes were changed or republished. See [SOURCES.md](SOURCES.md) for provenance and usage terms. Published inputs may be reused at their original paths. The hidden split remains runtime-isolated but visible to repository readers; it is not a secret evaluation set.

Read-only references: `tasks/agentic-search` for corpus layout, build/query lifecycle and deterministic Recall scoring, and `tasks/long-pdf-evidence` for the current trajectory-judge backend. Intentional differences: no ReAct/BM25 starter, no embeddings or BM25, no external retrieval/reranking, and a broader audit of the embedding/BM25 bans and other task constraints; the reviewed task now also has a trajectory audit. The allowed Qwen generation models remain those in this package's resource document.

## Validation

From the repository root, restore inputs with `python scripts/download_assets.py --task agentic-search-vectorless`. Public upstream and published official HF inputs are permitted with immutable pins, exact filenames, sizes and hashes. Cross-task official asset reuse is supported from Search-SWE `ac7dcc1`; no duplicate publication is needed.

Use `python scripts/check_tasks.py tasks/agentic-search-vectorless`, `python scripts/download_assets.py --task agentic-search-vectorless --verify-only`, and `python -B -m unittest discover -s tasks/agentic-search-vectorless/tests -p 'test_*.py' -q`. Full trials use `scripts/run_task.sh --task agentic-search-vectorless` with locally configured agent, optional generation and verifier-judge credentials.

The October 15 Codex + OpenRouter `openai/gpt-6-luna`, effort `max`, trial produced **Gold Recall@5 = 0**, compliance audit **1**, and final reward **0**. The verifier rebuilt the index in 460.82 seconds and completed all 20 query invocations in 154.15 seconds, with valid outputs and no scoring errors. The agent exhausted its 7,200-second development budget, so Harbor records `AgentTimeoutError`; the saved submission still received a valid zero score. This is evidence of working execution and auditing, not of positive retrieval quality. No setting was weakened or trial repeated merely because of the score.

The job is `jobs/evaluations/agentic-search-vectorless/codex/openai/gpt-6-luna/max/attempt-1/2026-10-15__14-05-14/`. All 28 recorded package file hashes matched the evaluated revision before this documentation refresh; runtime files and instructions are unchanged. On October 17, against `ac7dcc1`, merge-ready checks, all 3 asset hashes, 22 task tests and the 174-test shared suite passed. Public and hidden query IDs and gold document IDs are disjoint. The author review is `contributing/dev/contribution-readiness/2026-10-17/REVIEW.md`.
