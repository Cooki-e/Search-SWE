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

Local assets are hashed in `assets.json`. Their remote revisions remain null
until publication; local verification works, but strict release checks report
the three unpublished asset pins. No remote revision is fabricated.

```bash
python scripts/download_assets.py --task biomedical-graph-retrieval --verify-only
python -m unittest discover -s tasks/biomedical-graph-retrieval/tests -p 'test_*.py' -v
python scripts/run_task.py --task biomedical-graph-retrieval --agent pi \
  --model deepseek/deepseek-flash --dry-run
```

The last command previews a launch and does not call a model. Validation evidence
and remaining unrun layers are recorded in `VALIDATION.md`.
