# Validation and completion evidence

Run commands from the target repository root, using Python 3.12+. Replace
`task-1-new` with the agreed task ID. These checks use the checkout's existing
tools; the skill does not bundle a second release checker or Harbor runtime.

## 1. Inspect the package before execution

- Compare each instruction requirement to an observable verifier check and a
  public self-test. Public limits must not exist only in hidden tests.
- Parse `task.toml` and `assets.json`; verify unique identity, correct mode,
  separate verifier, artifact paths, and all five CPU/GPU configuration points.
- Review all scaffold prose, budgets and empty files. An empty `files` manifest
  is valid only if the task genuinely needs no downloadable fixed inputs.
- Check both build contexts and mounts for hidden-data/solution leakage. Protect
  the grader and reward files from the submitted process; a UID declaration
  without actually using that UID when launching code is insufficient.

```bash
python scripts/check_release.py
python -m unittest discover -s scripts/tests -p 'test_*.py'
python scripts/download_assets.py --task task-1-new --dry-run
bash -n tasks/task-1-new/tests/test.sh
git diff --check
```

Also inspect untracked files with `git status --short` because `git diff` does
not include them. The release checker inspects structure and manifests, not
solvability, full Harbor schema compatibility, or reward correctness.

The current `scripts/tests/test_task_images.py` includes an explicit `GPU_TASKS`
inventory. Adding a GPU task may require updating that expected inventory as a
direct integration change, while retaining image/resource consistency checks.
Do not lower assertions to make a wrongly configured task pass. Download and
launch commands discover task IDs from `tasks/*/task.toml` automatically.

## 2. Assets, Compose, and images

After restoring authorized inputs with `scripts/download_assets.py`, verify
their SHA-256 checksums with `--verify-only`. The launcher checks only presence
and size, so it does not replace this step. Missing assets are a blocker for
runtime verification, not a reason to create empty files at the mount paths.

Compose files are Harbor overlays. Direct `docker compose config` needs a
temporary base service with an image (this check does not pull that image):

```bash
task=task-1-new
(
  set -eu
  base=$(mktemp)
  trap 'rm -f "$base"' EXIT
  printf 'services:\n  main:\n    image: busybox:1.36\n' > "$base"
  for phase in environment tests; do
    docker compose --project-directory "tasks/$task/$phase" \
      -f "$base" -f "tasks/$task/$phase/docker-compose.yaml" config -q
  done
)
```

This checks merged configuration, not file availability or actual isolation.
Build both contexts when Docker and the resource/download budget permit:

```bash
docker build -t "search-swe-local:$task-agent" "tasks/$task/environment"
docker build -t "search-swe-local:$task-verifier" "tasks/$task/tests"
```

GPU images target linux/amd64 with CUDA 13.0 userspace. GPU execution requires
a compatible NVIDIA host driver and Container Toolkit. With the documented
Harbor 0.22.0 Docker backend, `gpus = 1` alone fails preflight. The repository
launcher passes `--override-gpus 0`, while **both Compose overlays still request
the real GPU**. For direct Harbor runs on that backend use the same override;
do not falsify task metadata to work around it. Recheck this behavior if Harbor
changes. CPU tasks do not need the override or NVIDIA reservation.

## 3. Exercise grading and a fresh trial

Test in disposable containers/workspaces, not against host `/app`, `/tests`, or
`/logs`. Run a known-good submission and meaningful negatives: missing output,
malformed/duplicate IDs, command failure, timeout, and attempts to write reward
or read hidden labels. Validate finite scores, logs, process cleanup, and the
actual artifact transfer into the separate verifier. The scaffold's zero-only
test is not a grader and cannot establish solvability.

For Oracle validation, `solution/solve.sh` must contain a real known-good
implementation in an author-only task copy. Do not create a public answer
directory without approval. Alternatively use a separately prepared correct
submission through the same verifier interface. Optimization scores need not
equal one: compare to the agreed baseline/gates and explain the expected result.

For a coding-agent trial, first preview (no containers or API calls):

```bash
bash scripts/run_task.sh --task task-1-new --agent codex \
  --model MODEL_ID --dry-run
```

Use a real configured model ID. The Codex launcher needs
`AGENT_OPENAI_BASE_URL` and `AGENT_OPENAI_API_KEY`. A judge, if used, has its own
`VERIFIER_OPENAI_BASE_URL`/`VERIFIER_OPENAI_API_KEY`; task APIs are additional
resources, not those agent credentials. Pi's supported model/provider mapping
is version-specific in `scripts/run_task.py`. Export values or use an ignored
local `.env`; never commit them. The launcher does not support `--agent oracle`.

After prerequisites and authorization are satisfied, remove `--dry-run` and
set a fresh `--output jobs/task-1-new-validation`. The launcher uses one attempt
and no retries; its output directory is a jobs root, not a resume target.
Inspect the trial's actual reward, verifier logs, artifacts and setup failures.
After a failure, record the command and cause, make a relevant correction, then
rerun within the agreed budget. Stop on persistent infrastructure/permission
blockers rather than repeatedly consuming APIs or GPUs.

## Handoff

Report changed paths, mode, hardware/image selection, input provenance,
commands/results for each completed layer, expected versus observed scores,
and unrun layers with their blockers. Distinguish static, asset, build,
grader, known-good and coding-agent E2E results. Do not label the task ready
for release while placeholders or required runtime checks remain unresolved.
