# Task sparse-retrieval-pruning Environment

The task runs in a prebuilt CPU-only container. The submission works in
`/app`; task data and documentation are mounted read-only under `/task/data` and
`/task/docs`.

The formal data contains a large corpus, public development data, and a hidden
query split. The corpus must be processed in a streaming or bounded-memory
fashion; loading all document terms into Python dictionaries may exceed the
memory limit.

The runtime provides 1 CPU worker, 32 GiB memory, an 80 GiB declared storage
budget, and no GPU. Storage is not enforced by a kernel filesystem quota. NumPy and the
Python standard library are available. No transformer model, package download,
credential, external service, or network access is required for the formal run.

Submission indexing and retrieval logic must be implemented in Python. Bash is
allowed only as a thin entry-point wrapper around Python. Native submission
source and compiled native submission executables are not allowed.

The verifier runs the unpruned reference starter as the latency baseline. The starter
retains all corpus postings and performs no default DF, prefix, or other
posting-list pruning. Candidate wall time is compared with the starter wall
time measured by the verifier under the same workload and resource allocation.

The fixed corpus contains 1,000,000 documents. Each formal search invocation
processes the same 1,000 hidden queries; the public development set contains
200 queries. The verifier runs five measurement rounds with fresh processes. Odd rounds run
starter then candidate; even rounds run candidate then starter. It uses the
median of each system's five complete search wall times and divides the starter
median by the candidate median. Timing includes process launch, Python imports,
index loading, reading all queries, retrieval, output writing and process exit.
There is no separate warmup and the OS file cache is retained between calls.
Each round uses a fresh private output directory and temporary HOME/TMPDIR; the
built index and submission source are read-only during search. Do not write to
the index, reuse answers across invocations, or rely on files from earlier runs.
All required persistent state must be built from public inputs. The verifier
isolates accessible paths and clears temporary state between invocations.
Every candidate round must meet both quality floors; reported aggregate quality
is the arithmetic mean across rounds. Outputs are validated in every round.
Both positive finite timing medians are required; failures yield zero reward.

The candidate build is limited to 3,600 seconds, the reference build to 1,800
seconds, and each complete search invocation to 900 seconds. The overall
verifier budget is 16,200 seconds, covering builds, ten searches and the
integrity judge. Both systems use the same one-CPU affinity, 32 GiB memory
limit, one-thread library settings and isolation. New threads are blocked;
Python worker processes are monitored and the trajectory is audited. Thin
serial shell launch wrappers remain allowed. This protocol does not grant
permission to run additional workers.

Reward is `clip((s - 4)/12, 0, 1)` where `s` is the starter median divided by the candidate median, gated on quality and integrity.

The canonical Python is `/opt/conda/bin/python`. Both `python` and `python3`,
including in login shells, resolve to this runtime and its preinstalled NumPy.
The container sets BLAS/OpenMP thread counts to one before imports.
