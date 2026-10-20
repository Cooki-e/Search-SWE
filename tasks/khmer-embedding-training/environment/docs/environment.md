# Environment

The task uses Python 3.12 at `/opt/conda/bin/python` with CUDA-enabled PyTorch, Transformers, SentenceTransformers, FlagEmbedding, NumPy and FAISS GPU. One NVIDIA A100 with 40 GiB GPU memory is available, together with 8 CPU cores, 32 GiB RAM and 100 GiB working storage.

The supplied data and models are mounted read-only under `/task/data` and `/task/models`. Work under `/app`. Use `/opt/conda/bin/python` when running Python.
