# Structured-source to request audit — v0.1.2

The request uses concise prose and the two build/run command examples requested
by the user. The benchmark name and record counts are omitted.

| Public condition | Request location | Implementation |
| --- | --- | --- |
| Executable court-case retrieval; supported/refuted/all; all means either | Opening paragraph | Frozen query stances and relevance judgments |
| Corpus, examples directory and supplied model path | Inputs paragraph | Public data/model mounts |
| Runtime, model/API policy and retrieval integrity | Linked resource documents | Resource allowlist, filtered credentials, trajectory audit |
| 6-hour agent phase; /app artifacts; read-only /task and verifier /app | Submission paragraph | task.toml, mounts and submission UID |
| Executable build; 3,600 seconds; required services started in build | Build command and following sentence | build timeout; separate verifier |
| Whole query batch; 20 seconds; exit 0 | Run command and following sentence | Single timed invocation |
| One output per query; ten distinct known IDs; finite descending scores | Output paragraph | validate_output |
| Mean NDCG@10; failed/late/invalid/audit failures receive zero | Final paragraph | Deterministic metric and integrity gate |

The user's explicit revision request overrides the generic instruction-rewrite
rule to copy every author-side scoring detail into the request. The numerical
baseline and reward-normalization formula are intentionally absent from the
agent prompt, but remain unchanged in the grader and author README. Annotation
scope and training-label limitations likewise remain in author documentation;
the prompt does not tell the agent to discover or repair particular data issues.
Batching and development-split suggestions were removed. No new runtime
restriction or scoring rule was introduced.

The v0.1.0 instruction and validation fingerprints are preserved under the
workspace's author-only `package-build/revisions/v0.1.0-before-instruction-trim`.
No coding-model evaluation of either instruction revision is claimed.

In v0.1.2, the visible data directory is `examples`, public IDs use the `example_` prefix, and resource documentation states available inputs and restrictions without suggesting a model-optimization method. The original source split and its audit records remain author-side.
