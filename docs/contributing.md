# Contributing to Search-SWE

Contributions to task packages, shared images, launchers, tests, and
documentation are welcome. Keep each change focused and preserve unrelated
work in the repository.

## Task contributions

For a new task or a substantial task revision, start with the repository-local
[contributor workflow](../.agents/AGENTS.md) and the
[`create-searchswe-task` skill](../.agents/skills/create-searchswe-task/SKILL.md).
The `.agents/` directory contains skills, references, and helpers for
agent-assisted contributions. Compatible agent harnesses can invoke
`$create-searchswe-task`; other environments can read the skill directly.

The skill covers task design, CPU/GPU scaffolding, fixed inputs, verifier
isolation, and staged validation. Reuse the shared images described in
[`docker/README.md`](../docker/README.md) rather than creating task-local copies
of the common runtime.

## Contribution rules

- Do not commit API keys, downloaded task inputs, hidden verifier data, job
  outputs, or author-only solutions.
- Keep task instructions, resource documentation, runtime configuration, and
  verifier behavior consistent.
- Keep `README.md` and `README_zh.md` aligned when changing shared user
  documentation.
- Treat website updates, dataset publication, image publication, and PR merges
  as separate actions that require explicit coordination.

## Validation

Run these repository-level checks before opening a pull request:

```bash
python scripts/check_release.py
python -m unittest discover -s scripts/tests -p 'test_*.py'
git diff --check
```

Task changes also require the applicable task-specific and runtime checks in
the skill's
[validation guide](../.agents/skills/create-searchswe-task/references/validation.md).
If you modify the skill or its scaffolder, run:

```bash
python .agents/skills/create-searchswe-task/scripts/test_scaffold_task.py
```

In the pull request, summarize the scope, list the commands and results, and
identify checks that were not run because they require external data, GPU
hardware, credentials, or paid APIs.
