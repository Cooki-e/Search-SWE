# Finalization and merge

## Complete the reviewed package

Each task lives at `tasks/<task-name>` in the contribution branch, with canonical
`task.name = "search-swe/<task-name>"` and actual authors. A PR may contain multiple
uniquely named tasks. Check names against the current base and queued PRs, and
update against the base while preserving original author commits. Record the
reviewed head and base; when either changes, review the new diff and rerun the
affected validation layers.

Resolve contributor branch-edit permissions, then apply review fixes and directly
necessary integration changes in the same PR. Check instructions, relative
mounts, images, external URLs, task inventories and GPU test inventories. Use
actual maintainer identity for maintainer commits and preserve task authors.
For a writable contributor fork, these commits go directly to the existing
PR's source branch; follow [contributor branch editing](pr-review.md#contributor-branch-editing).

## Publish assets and validate the final revision

Read [publication.md](publication.md) and verify existing official asset pins.
For files awaiting publication, first download and hash-check the contributor's
inputs using the original pinned manifest. Map the verified additions to official
`tasks/<task-name>/...` paths and use the bundled offline HF helper to stage them,
preserving existing manifest entries, model pins and provenance/license metadata.
Set `REPO` to the trusted checkout and `SKILL_DIR` to this installed skill. The
helper requires Python 3.12+ and an explicit `--repo-root`; it validates paths
and hashes locally.
Official publication and HF PR merge each require authorization.

When publication is needed, merge the official HF change first, then pin its
resulting 40-hex commit in `assets.json` and verify clean downloads. For each task,
record the final instruction revision, configured model/effort, trajectory,
score, judge health and feedback-driven corrections. Revalidate substantive task or scoring changes
within the authorized runtime budget. For source-path or pin-only updates with
identical asset hashes and unchanged task behavior, retain the completed model
trial, verify fresh official downloads and static checks, and record why that
evidence still applies to the final revision.

Run the audited target tools and applicable runtime layers:
`check_release.py`, `check_tasks.py --merge-ready --base FULL_PR_BASE_SHA`,
repository tests, changed skill regression tests, task-specific cases and
`git diff --check`. Review and commit the final asset pins and integration
changes in the same PR when authorized. Before an authorized push, verify that
the remote branch still matches the reviewed starting head and use a normal
push. Collect fresh review and check evidence for the resulting head.

## Commit asset pins to the contributor's PR branch

After the official HF change has merged, update the published entries in
`tasks/<task-name>/assets.json` in the isolated PR checkout: official repo ID,
published filenames and the actual merged 40-hex SHA. Keep task-relative paths,
sizes, hashes, model-repository sources and bundled metadata intact. Complete
fresh official downloads and the checks above before committing.

Use the verified PR head repository URL and branch from
[PR review](pr-review.md#contributor-branch-editing), and the existing scoped
commit/push authorization. In this example, set `task_name`, `head_repo_url`,
`head_branch` and `reviewed_head` to the reviewed values. The local commits must
descend from that starting head. Stage any additional reviewed fixes explicitly.

```bash
set -euo pipefail
git -C "$REPO" diff -- "tasks/$task_name/assets.json"
git -C "$REPO" add -- "tasks/$task_name/assets.json"
git -C "$REPO" diff --cached
git -C "$REPO" diff --cached --check
git -C "$REPO" commit -m "Pin $task_name assets to the official dataset"
remote_head=$(git -C "$REPO" ls-remote --refs "$head_repo_url" "refs/heads/$head_branch" | cut -f1)
if [ "$remote_head" = "$reviewed_head" ]; then
  git -C "$REPO" push "$head_repo_url" "HEAD:refs/heads/$head_branch"
else
  echo "Contributor branch changed; fetch and review its new head before pushing." >&2
  exit 1
fi
```

Use a normal push so a concurrent incompatible update is rejected. If the
contributor's branch advanced, reconcile and re-review while preserving both
authors' commits. After pushing, query the original upstream PR and confirm its
`headRefOid` equals the local `HEAD`; collect checks for that new head. If branch
editing is unavailable, hand off the reviewed commits or patch for the
contributor to apply and push to the same branch.

## Review, merge and verify

Prepare a review summary locally by default. Only post a comment/review after
explicit authorization for its content, repo and PR. Example commands (replace
verified values and use a trusted body file):

```bash
gh pr comment PR --repo OWNER/REPO --body-file /path/to/reviewed-comment.md
gh pr review PR --repo OWNER/REPO --request-changes --body-file /path/to/review.md
# Or --approve only when the head is actually accepted and posting is authorized.
```

Re-query the full head/base immediately before posting or merging; new commits
invalidate prior approval. The gh review command has no match-head flag: bind
review evidence to its full SHA, check again after posting, and resolve any race
rather than claiming acceptance of the changed head. All required human reviews,
resolved conversations, `review-stage`, `merge-ready` and other configured checks
must pass for that exact head and current base. Missing/pending checks block.
If protections/merge queue prevent the specified method, stop, do not bypass.

After explicit merge authorization and fresh head/base/name checks:

```bash
gh pr merge PR --repo OWNER/REPO --merge --match-head-commit FULL_REVIEWED_HEAD_SHA
```

**Merge commit only**: no `--squash`, `--rebase`, `--admin`, auto-merge shortcuts
or branch deletion unless separately requested. `--match-head-commit` guards the
head; coordinate against the current base as well. Never silently configure
protections, a queue or CODEOWNERS identities.

Close the loop after the command, rather than treating exit zero as proof:

1. Query `gh pr view PR --repo OWNER/REPO --json state,mergedAt,mergeCommit,headRefOid,baseRefName`.
   Confirm MERGED and record the full merge SHA; if queued/not merged, report that.
2. Fetch the resulting base/merge into the disposable checkout. Verify the merge
   object has two parents, the accepted PR head is its second parent, the reviewed
   base is its first parent, and original author commits are ancestors. Unexpected
   parent/base/tree changes require investigation, not a success claim.
3. Inspect the merged tree for `tasks/<task-name>/task.toml`, actual authors, final
   official pins and intended files.
   Compare it with the reviewed final tree (account for reviewed base integration).
4. Check `git log --follow -- tasks/<task-name>/instruction.md` and
   `git blame tasks/<task-name>/instruction.md` at the merge SHA. Original unmodified
   lines should retain contributor attribution. GitHub's latest file author and
   contributor statistics are not substitutes; stats also depend on linked email.
5. Report repo/PR, reviewed head/base, merge SHA, final path, official HF SHA,
   check/runtime evidence and author/history outcome. Do not retire personal
   development assets until verified official downloads work.
