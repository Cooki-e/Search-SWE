---
name: create-searchswe-task
description: Create or substantially revise Search-SWE task packages with CPU/GPU environments, fixed inputs, agent instructions, and a separate verifier. Use when contributing tasks, not merely running an existing task.
---

# Create a Search-SWE Task

Deliver a reproducible task whose instructions, environment, submission
interface, and grading agree. This skill contains its authoring guidance and
helpers; no outer AGENTS.md, other skill, or historical Harbor workspace is
required. It still operates on a **target Search-SWE checkout**: its tasks,
Docker definitions, and release/download/launch tools are project inputs, not
bundled copies of this skill. Missing tools or incompatible versions are
prerequisites to report, not permission to invent a replacement workflow.

## 1. Establish the design

Read [references/task-authoring.md](references/task-authoring.md). Inspect the
target checkout's status and preserve unrelated changes. Resolve its root
explicitly; do not infer it from where this skill was installed.

Record a short design summary before writing the package:

| Decision | What must be known |
| --- | --- |
| Identity | Unique task ID and name, author, version |
| Mode | Implementation → `metadata.task_type = "create"`; Optimization → `"optimize"` |
| Goal | What working capability or quality/efficiency improvement is measured |
| Interface | Container input paths, commands, output paths/formats, artifact transfer |
| Evaluation | Metric, public gates, baseline if needed, failure/timeout behavior |
| Inputs | Public/hidden split, actual files, provenance, redistribution rights |
| Resources | CPU/GPU, memory/storage/time, network, permitted APIs/models |

Only these two engineering modes exist. CPU is the default; choose GPU for
actual GPU execution, not merely because model files are involved. Ask for
missing facts that change the design; do not invent labels, licenses, service
access, or quality thresholds. An Optimization task needs a meaningful supplied
starting system/model and comparison criterion, not only a different mode label.

## 2. Create or edit the package

For a new task, run the bundled helper using its **actual installed path**:

```bash
# Set these to real absolute paths; neither depends on the current directory.
SKILL_DIR=/path/to/create-searchswe-task
REPO=/path/to/Search-SWE
python "$SKILL_DIR/scripts/scaffold_task.py" task-1-new \
  --repo-root "$REPO" --mode implementation --hardware cpu
```

Use `--mode optimization` for optimization and `--hardware gpu` for GPU work.
The flags are independent. The helper refuses existing paths. Edit an existing
task in place instead; do not delete it to make the helper succeed.

The scaffold is **not a finished task**: its verifier always fails, its asset
manifest is empty, data/model mounts are absent, and instructions are writing
prompts. Replace them and review the generated budgets, author, artifact list,
and network settings. The shared image supplies common dependencies; add only
task-specific pinned packages to each Dockerfile. Both Dockerfiles must use
the matching CPU/GPU image, consistent with both Compose files and `gpus`.

## 3. Implement the contract

Follow the detailed rules in `references/task-authoring.md`:

1. Define the submission interface and grader behavior, then write an instruction
   containing every graded requirement. Do not reveal hidden answers.
2. When adding fixed data/models or external services, read
   [references/assets-and-resources.md](references/assets-and-resources.md).
   Build exact manifests and read-only phase-specific mounts. Keep hidden inputs,
   solutions, and judge credentials out of the agent environment.
3. Write visible environment/resource docs matching what is actually provided.
4. Implement the separate verifier: copy tests into its image, explicitly
   transfer submission artifacts, run untrusted code without grading privileges,
   bound execution, and initialize reward to zero. A separate container does not
   protect a grader from submitted code run as root inside that container.
5. Add author-facing README context and task-local tests, including known-good
   and invalid submissions. Do not change unrelated tasks or scoring policies.

## 4. Validate and hand off

Read [references/validation.md](references/validation.md) and follow its staged
checks. Stop advancing to expensive runtime tests when inputs, permissions,
hardware, or required configuration are missing. Record the failed command and
diagnosis; retry after a relevant fix, not in an unbounded loop.

Task authoring does not itself authorize publishing data/images, modifying host
network/proxy configuration, or spending on model APIs/GPU jobs. Obtain missing
authorization for those actions; ordinary local checks may proceed.

Report the task path, mode/hardware, commands actually executed and their
results, known-good/negative-case evidence, and every unrun validation layer.
Never equate a scaffold, a dry-run, or a static release check with a solvable
end-to-end task.

When modifying this skill or its scaffolder, run the bundled relocation and
generation checks: `python "$SKILL_DIR/scripts/test_scaffold_task.py"`. They use
temporary directories and do not build images or call APIs.
