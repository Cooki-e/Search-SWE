## Summary

Submission path (new task only): `task-submissions/<first-name-slug>/<1|2>-x`
Category / Implementation or Optimization / CPU or GPU:
Authors and coauthors:

## Validation evidence

List commands, actual results, and links to task-specific known-good/negative-case
results. List unrun checks and why (data, GPU, credentials, paid APIs).

## Contributor checklist

- [ ] One new task in this PR; no guessed final number or username namespace.
- [ ] Actual authors in `task.toml`; commit email associated with my GitHub account.
- [ ] Allow edits from maintainers; promotion stays in this same PR.
- [ ] No secrets, downloaded inputs/models, job outputs, or author-only solutions.
- [ ] Static package/submission checks and applicable runtime checks recorded.
- [ ] Asset provenance, redistribution rights, licenses and pinned development SHA documented.

## Maintainer merge checklist (new tasks)

- [ ] Design, verifier isolation and runtime evidence reviewed; exceptions explicitly approved.
- [ ] Updated to latest main; final number assigned serially without collision.
- [ ] Separate pure `git mv` commit, then reviewed finalization commit, in this PR.
- [ ] HF community PR or maintainer mirror merged into official dataset; manifest,
      SOURCES and license updated, all old assets preserved; official SHA pinned in `assets.json`.
- [ ] Repository inventories/docs updated; full checks and merge-ready gate pass;
      no submission `task.toml` remains.
- [ ] **Merge commit only** (no squash/rebase); contributor history retained.
