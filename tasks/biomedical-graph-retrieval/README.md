# Biomedical Graph Retrieval

Author: Cooki-e. Build a reusable search system over the supplied knowledge graph
and return complete sets of internal node IDs. No training or fine-tuning.

The local package includes the corpus, 3 public validation questions and 20
private test questions. Version 0.2.1 preserves the graph and private split and
provides three public examples with different query plans from the hidden set.
Both splits require multi-step graph computation and complete answers, verified
by independent calculations. Comparable difficulty is a structural judgment;
no fresh coding-agent score is available. Source attribution, licensing records and construction evidence are
retained separately in the authoring workspace; source dataset names are omitted
from this package.

`instruction.md` is the concise agent request; `raw-instruction.md` is its
structured equivalent. Resource and time limits are in the instruction and
`task.toml`. `environment/docs/environment.md` is an exact copy of the shared CPU
environment description. Agents inspect the supplied files to discover their
structure; no separate corpus guide or starter solution is provided.

The verifier runs submitted code as a non-root user, builds once, then runs each
hidden question sequentially with a 30-second deadline. It compares complete ID
sets deterministically. Timeout or wrong answer gives that question zero; failed
build, other execution errors or invalid output invalidates the submission.
A separate trajectory audit gates the final reward.

Only the corpus, public validation and generic resource documents are mounted
into the agent environment. Private questions, labels, grader and audit files
remain verifier-only. No author solutions or screening traces are supplied.

Public runtime data are published in [search-swe/Search-SWE](https://huggingface.co/datasets/search-swe/Search-SWE/tree/2a2188f3a9426361da5f10c82a35148269574a92) and pinned by immutable commit in `assets.json`, with exact sizes and SHA-256 hashes. Private evaluation inputs remain in the verifier package. Source terms and attribution remain applicable; publication does not establish additional licensing rights. Fresh restoration on 2026-10-16 verified all 3 dataset-backed runtime files against their recorded sizes and SHA-256 hashes.

```bash
python scripts/download_assets.py --task biomedical-graph-retrieval --verify-only
python -m unittest discover -s tasks/biomedical-graph-retrieval/tests -p 'test_*.py' -v
python scripts/run_task.py --task biomedical-graph-retrieval --agent pi \
  --model deepseek/deepseek-flash --dry-run
```

The last command previews a launch and does not call a model. Validation evidence
and remaining unrun layers are recorded in `VALIDATION.md`.
