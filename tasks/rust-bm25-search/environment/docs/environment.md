# Environment

CPU-only Linux x86_64: 4 CPUs, 16 GiB container memory including children and
page cache, 64 GiB workspace, 256 PIDs, no runtime network. Agent budget:
10,800 seconds. Both phases use
`docker.io/hanhainebula/search-swe-base:cpu-py3.12-1.0.0`.
The verifier host must provide Linux Landlock ABI 1 or newer.
Submitted commands additionally have a 128-process/thread UID limit and 1,024
file descriptors. Compilation/indexing output files are capped at 16 GiB each;
each search diagnostic file is capped at 16 MiB.

Rust 1.85.1 is installed at `/opt/rust`. `/opt/cargo` contains the locked
generic dependency cache. The starter at `/app/submission` does not implement
retrieval. Use `cargo build --release --offline --locked`.
`CARGO_TARGET_DIR=/app/build` keeps build products outside submitted source.
After implementing the CLI, run `python /task/smoke.py --binary
/app/build/release/bm25-search` for a three-passage synthetic check. It does
not estimate full-dev quality or add a hidden score requirement.

Only `/app/submission` transfers. The verifier recompiles it within 600 seconds
and rebuilds the index from the raw corpus within 7,200 seconds. Submit only
Cargo.toml, Cargo.lock, Rust files under src, and optionally README.md.
Commands are `bm25-search index --corpus PATH --index DIR --threads 4` and
`bm25-search search --index DIR --threads 4`. The task request defines the
complete protocol, measurement procedure and file limits.

Search runs as UID 10001. It can read the immutable index, executable and
necessary system libraries; raw corpus and writable caches are unavailable.
Each cold sample starts a fresh process without query warmup. OS file caches
are not cleared. Stdout is JSONL only; diagnostics may use stderr.

The shared image includes additional software such as Pyserini. Availability
does not permit using an existing search engine in the submission. The
reference is Pyserini 1.4.0 with BM25 k1=0.9, b=0.4. Verification requires no
API credentials or model judge.
