# Long-PDF Sentence Evidence Retrieval

Retrieve up to five original sentence units that fully support a short interpretive question about *War and Peace*. Version 0.4.1 uses **SentenceEvidenceAccuracy**. The old 0.95 page-retrieval result is not a measurement of this revised task.

The unchanged PDF has 2,043 physical pages. Its question-independent inventory contains 28,798 units, preserving source-page provenance and normalizing PDF typography and whitespace. Unit boundaries are fixed for consistent evaluation, including dialogue and sentences crossing pages. The ten public and twelve hidden questions use disjoint reference units and opaque shuffled IDs. Questions ask about motives, tensions, reversals, or relationships without restating the relevant passage.

| Input | Role |
| --- | --- |
| `data/corpus/lp4P6AUxur.pdf` | Original shared novel |
| `data/corpus/sentences.jsonl` | Fixed sentence text, opaque IDs, physical source pages |
| `data/validation/queries.jsonl` | Ten public questions |
| `data/validation/golden_answers.jsonl` | Public support requirements and sufficient original evidence |
| `tests/data/` | Twelve private queries and references, excluded from agent mounts |

Deliver executable `/app/build.sh` and `/app/run.sh` following [instruction.md](instruction.md). Return `{query_id, results: [{sentence_id, sentence}]}`, with zero to five distinct units and no generated answer. Evidence order is irrelevant. The verifier checks corpus checksums, source membership, and output validity before judging sufficiency. Alternative correct evidence is accepted; reference IDs are not a scoring gate.

The answer judge is pinned to OpenRouter `openai/gpt-6-luna`, reasoning effort `high`, temperature 0. It awards 1 for complete evidence support and 0 otherwise. Mean support over all twelve questions is the metric; a failed or timed-out query remains in the denominator with zero. API/parse failures invalidate the measurement and fail closed, separately from ordinary unsupported evidence. A separate existing `deepseek/deepseek-v4.1-flash` trajectory audit through RewardKit 0.2.0 gates the final reward. Judge health and individual decisions are retained in verifier reports.

The CPU environment supplies 16 CPUs, 64 GiB memory, 100 GiB storage and no GPU. Development lasts at most two hours. Build receives 2,400 seconds; each query receives 900 seconds, with concurrency five and a shared 1,800-second query phase. The outer runner permits 60 seconds for cleanup. Answer judging is bounded at 2,700 seconds, with two workers, at most two attempts per request, and 10-second connect / 120-second read timeouts. Trajectory auditing is bounded at 3,600 seconds; the whole verifier allows 10,800 seconds. These resources and query limits are unchanged from the previous task.

Submission processes run as an unprivileged user. The verifier stages only the fixed corpus and query inputs for them, excludes judge credentials from their environment, terminates submission processes before judging, and protects private labels and reward files. `/app` is transferred into a fresh environment; service processes must be recreated by the build. See the [resource policy](environment/docs/available_resources.md) for the unchanged solver API allowlist. The semantic judge does not authorize solvers to call Luna.

For local runs, configure an OpenRouter credential in `ANSWER_JUDGE_API_KEY`; the task pins `ANSWER_JUDGE_BASE_URL` and `ANSWER_JUDGE_MODEL_NAME`. Keep the trajectory judge's separate `VERIFIER_OPENAI_*` configuration. Optional solver APIs use `OPENROUTER_API_KEY` and `JINA_API_KEY`. Never store keys in the task package. The shared launcher accepts `--task long-pdf-evidence --model YOUR_AGENT_MODEL`; `--dry-run` only inspects command construction.

The original PDF retains its published immutable revision. The new inventory and revised public examples are locally staged, with honest null publication revisions in [assets.json](assets.json); they must be published and pinned before release. Local checksum verification works with these files present. Downloading from the old published revision cannot restore the new assets. No new license or publication permission is asserted by this revision.

Author development and calibration records live outside the package in `task_development/long-pdf-evidence` in the surrounding build workspace. [raw-instruction.md](raw-instruction.md) is the structured contract; [instruction.md](instruction.md) carries the same requirements in the agent-facing request. The prior task supplies the corpus, executable lifecycle and isolation pattern; `scientific-paper-qa` was consulted for separate semantic-judge credentials. The requested `agentic-search` reference currently uses deterministic GoldRecall@5, so its grader is not a semantic-judge implementation.
