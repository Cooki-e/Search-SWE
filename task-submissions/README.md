# Task submissions: review buffer, not a task registry

Create new tasks at `task-submissions/<first-name-slug>/1-x` or `2-x`, with the
internal canonical ID `task-1-x` or `task-2-x`. Use a contributor-supplied first
name, **not a username**: `Alice` → `alice`, `Mary Jane` → `mary-jane`. For a
non-Latin name, supply your preferred ASCII transliteration. Slugs match
`[a-z][a-z0-9]*(?:-[a-z0-9]+)*`.

Check active PRs before choosing a namespace. If another active contributor
uses `alice`, use `alice-2`, then `alice-3`. The scaffolder handles collisions
visible in your checkout; it cannot see other open PR branches. A name is not
identity authentication or permanent credit; use real `task.toml` authors and
correct Git author metadata.

```bash
python .agents/skills/create-searchswe-task/scripts/scaffold_task.py task-1-x \
  --submission-first-name Alice --author 'Alice Example' \
  --mode implementation --hardware cpu
python scripts/check_submission.py task-submissions/alice/1-x
python scripts/download_assets.py --task-path task-submissions/alice/1-x --dry-run
python scripts/run_task.py --task-path task-submissions/alice/1-x \
  --agent pi --model deepseek/deepseek-flash --dry-run
```

A scaffold intentionally fails verification until implemented. `--task all`
only discovers formal `tasks/*/task.toml` packages; submissions need explicit
`--task-path`. Read the [complete contribution guide](../docs/contributing.md).
One new task per PR; no submission is merged unfinished. A maintainer performs
pure rename, then finalization in that same PR before a **merge commit**.
This README stays on main; submission task packages do not.
