# CPU Docker Environment

This image provides a Conda-managed Python 3.12 environment with CPU-only PyTorch and the common search, embedding, indexing, document-processing, media, HTTP, and service packages used by the tasks. Installed Python packages include `torch`, `torchvision`, `torchcodec`, `numpy`, `transformers`, `sentence-transformers`, `FlagEmbedding`, `deepspeed`, `faiss-cpu`, `bm25s`, `rank-bm25`, `pyserini`, `hnswlib`, `qdrant-client`, `docling`, `marker-pdf`, `pdf2image`, `pypdfium2`, `CairoSVG`, `av`, `imageio`, `imageio-ffmpeg`, `tiktoken`, `fastapi`, `uvicorn`, `python-multipart`, `requests`, `aiohttp`, `openai`, and `pydantic-settings`.

The task Python interpreter and its installed packages are available at `/opt/conda/bin/python`. Use `/opt/conda/bin/python` and `/opt/conda/bin/pip` when invoking Python or installing packages.

The image also includes JDK 21, FFmpeg, Poppler utilities, Cairo, Git, curl, `jq`, `build-essential`, `ca-certificates`, `libffi`, `libgomp`, `netbase`, `netcat`, `procps`, `tzdata`, `unzip`, and the related system runtime libraries.

## Task resources and execution limits

The task provides 4 CPUs, 32 GiB RAM, 100 GiB storage and no GPU. The Agent phase allows 120 minutes for implementation, validation and debugging.

During verification, `build.sh` must complete within 1,800 seconds. After that single build, the verifier invokes `run.sh` sequentially, once per query, with exactly one query row in each input file. Each invocation must finish within **8 seconds of wall-clock time**: a 3-second base budget plus a fixed 5-second allowance for network/API overhead. This single deadline includes process startup, index loading, parsing, retrieval, generation, all API waits and retries, filtering, reranking and output. The allowance applies once per query, not once per API call; API wait time is not separately measured or subtracted. Unused time cannot be pooled across queries. Both commands must return exit status 0 to count as successful. A query that times out earns zero for that query; its output is ignored and evaluation continues with the remaining queries. Timed-out queries stay in the denominator of Accuracy@1. Build failures/timeouts and other execution/output violations still invalidate the submission.

The same index directory and any build-started background service are available between query invocations, including after a query timeout. A timeout terminates the current query process group, not build-started services. Each invocation receives distinct input and output paths so late responses cannot be reused for another query. Future evaluation queries are not revealed in advance. Prepare reusable artifacts during the build. The 4-CPU limit controls local compute; it is not a limit on concurrent network requests.

## Verification environment

Verification uses a fresh, separate container with the same base runtime. Only `/app` is transferred; packages installed elsewhere during development do not transfer. Keep all required code, dependencies and resources under `/app`.

The submission runs as a non-root user with `/app` read-only. The verifier supplies a fresh writable `--index-dir`; use it for indexes, caches, temporary files and service state. The result file is written separately at `--output`. Honor `TMPDIR` and the supplied paths, which may differ from development paths. Public validation files need not be available during verification.
