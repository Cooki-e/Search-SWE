# Validation — version 0.2.1

Version 0.2.1 replaces the twenty public examples with three newly constructed
questions. Their query plans differ from all six private families: minimum
two-drug target cover, induced connected-component profiles, and deepest drug
synergy cores. Complete answer sets agree between separate Python/SQL or
Python/NetworkX calculations. Public query anchors do not overlap private query
anchors, and no public complete answer set equals a private complete answer set.
The twenty private questions and labels remain byte-identical to version 0.2.0.
Graph, scorer, instruction, executable interface and resource limits are unchanged.

The public examples are intended to require comparable reasoning and programming
effort without exposing private templates. This is a structural design judgment,
not measured coding-agent difficulty. The previous twenty public examples and
the rejected same-family draft remain outside the runtime task package.

The following model and runtime results concern earlier versions; they do not
constitute a new model evaluation of version 0.2.1.

The v0.1.1 full Codex/OpenRouter openai/gpt-6-luna max run scored 19/20
(0.95), with a passing trajectory audit. This supersedes the earlier fixed
per-query-baseline difficulty claim. Public examples exposed nearly all query
forms implemented by that submission.

Version 0.2.0 replaced all 20 private questions. At that revision, the complete
graph and both public validation files were unchanged. Scoring, budgets, API permissions,
container boundaries and executable interfaces are unchanged. The instruction
and structured source both clarify generalization beyond illustrative examples.

All 20 complete answer sets agree between independent computations (SQL joins
versus set enumeration, or NetworkX path algorithms versus custom BFS/counting).
Every question has recorded near misses and semantic review outside the task.
The new query/label files were frozen before evaluating the saved submission
or running a new Coding Agent.

Offline production-verifier checks completed: the author reference returned
20/20 exact sets (maximum query time 1.17 seconds), and the archived submission
returned 0/20 with valid output and no timeout. These checks had no audit API;
their deterministic accuracies are not final audited rewards. The saved replay
does not establish difficulty for a fresh Coding Agent.

A new Coding Agent run was stopped at the user's instruction before submission
or final scoring. No new full-agent difficulty score is available. Further
Harbor or paid-model evaluation requires an explicit user request. The three
unpublished remote asset pins remain a separate release limitation.
