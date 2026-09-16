# Search-SWE Contributor Workflow

This is the contributor workflow entry point. Detailed task-authoring knowledge
lives inside the skill, not here. Paths below are relative to the repository
root unless expressed as Markdown links.

## Route the request

- **Create or substantially revise a task:** load
  [create-searchswe-task](skills/create-searchswe-task/SKILL.md) and follow its
  workflow, references, and validation gates. If no native skill loader is
  available, open that `SKILL.md` directly. It can also be invoked independently
  as `$create-searchswe-task`; it does not need this file.
- **Run an existing task:** use `docs/quickstart.md`; do not scaffold a task.
- **Restore fixed inputs:** use `docs/assets.md` and the existing download tools.
- **Edit project documentation:** keep `README.md` and `README_zh.md` aligned.
  The current public modes are Implementation and Optimization.
- **Change shared images:** use `docker/README.md`. An ordinary task contribution
  should reuse the CPU/GPU images rather than redesign their shared runtime.

## Coordinate the work

1. Inspect the worktree and agree on the requested deliverable. Preserve other
   contributors' changes. Ask about uncertainties that affect task design or
   authorization, not information already supplied by the user.
2. For task contributions, let the skill drive design → authoring → validation.
   Track which stage is complete and which inputs or approvals are missing.
   Do not duplicate the skill's specifications in this file.
3. Keep changes within the selected task plus directly necessary integration
   changes. Updating a website, publishing a dataset, pushing images, and opening
   or merging a PR are separate actions, not implied by task creation.
4. Review the resulting diff and validation evidence. Hand off changed paths,
   task mode/hardware, commands actually run, observed results, and blockers.
   Static checks alone are not evidence of a working end-to-end benchmark.

Agents are not guaranteed to auto-load an `AGENTS.md` located under `.agents/`
when editing `tasks/`. Open this entry point explicitly or invoke the skill;
do not assume its directory placement grants repository-wide instruction scope.
