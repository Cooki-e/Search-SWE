# Filtered ANN retrieval

Author: **bingyu**. Version: **0.10.0**. Migrated from
`search_swe_bingyu/task-submissions/bingyu/1-x-1` version 0.8.1.

Build a persistent Faiss ANN backend returning exact nearest neighbors subject
to conjunctions of metadata tags. CPU only; no embedding model or retrieval API.

## Data and provenance

The corpus has 10,000,000 192-dimensional uint8 vectors and CSR metadata with
200,386 tag columns. Ten public and ten disjoint hidden queries each contain
four single-tag, four two-tag and two three-tag filters. A separate 64-document,
17-query example supports functional development without adding scored cases.

All retained data and labels are byte-identical to the source task. `assets.json`
pins eight public assets in [the official Search-SWE dataset](https://huggingface.co/datasets/search-swe/Search-SWE/tree/2182510dda66f946a153a5b09515f82fb4da125e/tasks/filtered-ann-retrieval)
at immutable revision `2182510dda66f946a153a5b09515f82fb4da125e`, under
`tasks/filtered-ann-retrieval/`. The original source was
`Cooki-e/search-swe-development@d82ef21a21cecab959c77a7133e0ab00146a8318`,
under `development/bingyu/1-x-1/`. See [SOURCES.md](SOURCES.md) for provenance and
license qualifications.

```bash
python scripts/download_assets.py --task filtered-ann-retrieval
python scripts/download_assets.py --task filtered-ann-retrieval --verify-only
python scripts/check_tasks.py tasks/filtered-ann-retrieval
```

Runtime `data/` is ignored by Git. The agent receives corpus, public examples and
docs. Hidden queries, labels and the grader are copied into the separate verifier
image. Reference implementations remain outside the task package.

## Interface and scoring

See [instruction.md](instruction.md) and its structured source
[raw-instruction.md](raw-instruction.md).

- `/app/build.sh --vectors PATH --metadata PATH --index-dir PATH`: build a fresh,
  trained Faiss ANN index covering the corpus within 600 seconds.
- `/app/run.sh --index-dir PATH --serve`: load, emit a ready JSON line, and serve
  individual JSON requests over stdin/stdout, each within 15 milliseconds.
- Filters use AND semantics; distance is original-vector squared L2. Results must
  be complete exact Top-10, ordered by `(distance, doc_id)`. Boundary ties count.
  Output contains document IDs; the verifier computes distances independently.
- Each hidden query is checked before and after index relocation. It earns one
  only if both responses are correct, timely and identical. The retrieval score
  is the mean of ten binary scores, not the mean of twenty independent requests.
- Request failures affect only that query. Protocol failures trigger a restart
  so late replies cannot contaminate later queries. Build, index or service-load
  failures invalidate retrieval. The required trajectory audit gates final
  reward and fails closed when absent or unsuccessful.

Timing includes request transmission and response JSON decoding. Service startup
is outside this timer with no independent timeout; the entire retrieval phase
has a 3,900-second supervisor deadline.

## Runtime and migration

8 CPUs, 16 GiB RAM, 64 GiB storage, no GPU; implementation time 120 minutes.
Both images use `search-swe-base:cpu-py3.12-1.0.0`. Agent and submitted search code
are offline. The verifier permits OpenRouter solely for the root-side audit;
submission processes use UID 10001, a clean environment and a seccomp network block.

Migration updates the task ID, removes obsolete `metadata.task_type`, pins current
agent CLIs and adopts the repository RewardKit 0.2.0 / DeepSeek V4.1 Flash wrapper.
The original audit criteria, exact-ranking score and latency gates are preserved.
Version 0.10.0 removes unused corpus/config.json, strips implementation advice
from visible docs, and requires IDs only instead of returned distances with a
0.001 tolerance. Binary-format documentation retains only the input schema.
Structural precedents are `memory-constrained-dense-retrieval`
and `sparse-retrieval-pruning` for offline CPU retrieval and protected evaluation.

## Validation

See [VALIDATION.md](VALIDATION.md) for executed checks and unrun layers. Detailed
migration reports live outside the package in
`task_development/filtered-ann-retrieval/migration/`.

No paid coding-model or live judge call was made for this migration. Reference
runs measure raw retrieval; without the required audit, final reward remains
zero. Official asset publication and release checks are recorded separately
from local migration in [VALIDATION.md](VALIDATION.md).
