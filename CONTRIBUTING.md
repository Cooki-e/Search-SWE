# Contributing to Search-SWE

Start with the [contribution guide](docs/contributing.md) for the complete task
workflow, validation commands, asset publication, and maintainer merge checklist.
For agent-assisted authoring, use the
[create-searchswe-task skill](.agents/skills/create-searchswe-task/SKILL.md).

New tasks belong in `task-submissions/<first-name-slug>/1-x` or `2-x`, **not** in
`tasks/`. Use your chosen ASCII first name, not your GitHub username. One new
task per PR. Maintainers assign the final number and promote the task in the
**same PR**, with a pure rename commit followed by finalization. New-task PRs
must use a **merge commit**, never squash or rebase merge.
