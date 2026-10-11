# Instruction equivalence review

Reviewed `raw-instruction.md` against `instruction.md`. The latter is the sole
agent-facing request and uses connected prose without headings, lists, tables
or fenced code. No hidden query, qrel, retrieval answer or author solution is
exposed in either instruction.

| Structured source | Request paragraphs | Implementation/evidence |
|---|---|---|
| Work need and engineering objective | 1 | `tests/evaluate.py:tradeoff_reward` |
| Corpus, text-only field, IDs, warmup, held-out split, terms | 2 | Asset pins; converter ID/count audit; overlap check |
| Hardware, budgets, toolchain, offline starter and optional toy check | 3 | Dockerfiles, Compose, task.toml, locked cache, `environment/smoke.py` |
| Self-built Rust components and permitted generic crates | 4 | Source-only recompilation; author/source audit still required |
| No engine, neural retrieval, external data or answer tables | 4 | Offline execution and filesystem controls; review remains necessary |
| Artifact files, size/count, Cargo command and limits | 5 | `tests/grader.py:copy_source`, `build_submission` |
| Empty index, full rebuild, time/disk/workspace limits | 6 | `tests/grader.py:build_submission` |
| Persistent JSONL, IDs, scores, ties, byte limits, EOF | 7 | `tests/benchmark.py`, `tests/evaluate.py` |
| Unprivileged execution and index-only search | 8 | `tests/isolate.py`, root-owned input/index/log directories |
| Pinned reference and exact MRR denominator/floor | 9 | `tests/reference-quality.json`, rational quality comparison |
| Fresh cold processes, OS cache caveat, warmup, deadlines | 10 | `tests/benchmark.py:measure` |
| Disk accounting, RSS scope, reported metrics, concurrency | 11 | `index_bytes`, controller timestamps and `/proc` samples |
| Local reference, weights, formula and failure semantics | 12 | `tests/grader.py`, `tests/evaluate.py` |

The cold definition is fresh-process/no-query-warmup, including process launch;
it makes no promise of physical cold I/O. Quality is a hard exact gate. The
draft uses equal quality/time/disk weights; cold and RSS remain explicit report
fields, with runtime/resource bounds. Throughput is not counted twice.

Some obligations require source/trajectory review: the implementation must
actually be self-built Rust BM25, not hide an existing engine or hard-coded
answers. A deterministic score alone cannot prove that provenance.
