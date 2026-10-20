# Environment

The task uses Python 3.12 at `/opt/conda/bin/python` with CUDA-enabled PyTorch, Transformers, SentenceTransformers, FlagEmbedding, NumPy, and FAISS GPU. One NVIDIA GPU is available.

Task data and the supplied backbone are mounted read-only at `/task/data` and `/task/models`. Work under `/app`. Use `/opt/conda/bin/python` when running Python.
