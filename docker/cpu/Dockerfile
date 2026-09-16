FROM python:3.12.14-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/cache/huggingface \
    CONDA_DIR=/opt/conda \
    JAVA_HOME=/opt/java/openjdk

ENV PATH=/opt/conda/bin:/opt/java/openjdk/bin:/usr/local/bin:$PATH

ARG TARGETARCH=amd64

RUN set -eux; \
    test "$TARGETARCH" = "amd64" || { \
        echo "Unsupported architecture: $TARGETARCH" >&2; \
        exit 1; \
    }

# ---------------------------------------------------------------------------
# System runtime and build dependencies
# ---------------------------------------------------------------------------

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        jq \
        libcairo2 \
        libffi-dev \
        libgomp1 \
        netbase \
        netcat-openbsd \
        poppler-utils \
        procps \
        tzdata \
        unzip \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------------------------
# Miniforge + FAISS CPU
# ---------------------------------------------------------------------------

ARG MINIFORGE_VERSION=25.3.0-3
ARG MINIFORGE_SHA256=1b57f8cb991982063f79b56176881093abb1dc76d73fda32102afde60585b5a1

RUN set -eux; \
    miniforge="/tmp/Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh"; \
    curl --fail --silent --show-error --location --http1.1 \
        --retry 8 --retry-all-errors --retry-delay 5 \
        "https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh" \
        --output "$miniforge"; \
    echo "${MINIFORGE_SHA256}  ${miniforge}" \
        | sha256sum --check --strict; \
    bash "$miniforge" -b -p "$CONDA_DIR"; \
    rm -f "$miniforge"; \
    conda install -y \
        --override-channels \
        -c pytorch \
        -c conda-forge \
        python=3.12 \
        faiss-cpu=1.15.0; \
    conda clean -afy; \
    python --version; \
    python -c 'import faiss; assert faiss.__version__ == "1.15.0"; print("FAISS:", faiss.__version__)'


# ---------------------------------------------------------------------------
# Java 21 for Pyserini / Lucene
# ---------------------------------------------------------------------------

RUN set -eux; \
    java_arch="x64"; \
    java_sha256="8a379a67c91a3ae61ffb33d46e0a40c7ba35e70713c4db31cfca30492f792eff"; \
    java_archive="/tmp/OpenJDK21U-jre_${java_arch}_linux_hotspot_21.0.12_8.tar.gz"; \
    curl --fail --silent --show-error --location --http1.1 \
        --retry 8 --retry-all-errors --retry-delay 5 \
        "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12%2B8/OpenJDK21U-jre_${java_arch}_linux_hotspot_21.0.12_8.tar.gz" \
        --output "$java_archive"; \
    echo "${java_sha256}  ${java_archive}" \
        | sha256sum --check --strict; \
    mkdir -p "$JAVA_HOME"; \
    tar --extract --gzip \
        --file "$java_archive" \
        --directory "$JAVA_HOME" \
        --strip-components=1; \
    rm -f "$java_archive"; \
    java -version


WORKDIR /app

COPY requirements.txt /tmp/requirements.txt


# ---------------------------------------------------------------------------
# CPU-only PyTorch runtime
# ---------------------------------------------------------------------------

RUN python -m pip install \
        --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.9.0+cpu \
        torchvision==0.24.0+cpu \
        torchcodec==0.9.1


# ---------------------------------------------------------------------------
# Remaining Python dependencies
# ---------------------------------------------------------------------------

RUN python -m pip install \
        --no-cache-dir \
        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        --extra-index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r /tmp/requirements.txt \
    && python -m pip check \
    && rm -f /tmp/requirements.txt


RUN mkdir -p \
        /app \
        /logs \
        /cache/huggingface


# ---------------------------------------------------------------------------
# Node.js 24 and bundled npm (pinned to the versions installed on the host)
# ---------------------------------------------------------------------------

ARG NODE_VERSION=24.16.0
ARG NPM_VERSION=11.13.0
ARG NODE_LINUX_X64_SHA256=2faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff

RUN set -eux; \
    node_archive="/tmp/node-v${NODE_VERSION}-linux-x64.tar.gz"; \
    curl --fail --silent --show-error --location --http1.1 \
        --retry 8 --retry-all-errors --retry-delay 5 \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz" \
        --output "$node_archive"; \
    echo "${NODE_LINUX_X64_SHA256}  ${node_archive}" \
        | sha256sum --check --strict; \
    tar --extract --gzip \
        --file "$node_archive" \
        --directory /usr/local \
        --strip-components=1; \
    rm -f "$node_archive"; \
    test "$(command -v node)" = "/usr/local/bin/node"; \
    test "$(command -v npm)" = "/usr/local/bin/npm"; \
    test "$(node --version)" = "v${NODE_VERSION}"; \
    test "$(npm --version)" = "${NPM_VERSION}"


# ---------------------------------------------------------------------------
# System runtime checks
# ---------------------------------------------------------------------------

RUN set -eux; \
    test "$(command -v python)" = "/opt/conda/bin/python"; \
    command -v java; \
    test "$(command -v node)" = "/usr/local/bin/node"; \
    test "$(command -v npm)" = "/usr/local/bin/npm"; \
    command -v ffmpeg; \
    command -v pdftoppm; \
    command -v pdftocairo; \
    python --version; \
    java -version; \
    test "$(node --version)" = "v${NODE_VERSION}"; \
    test "$(npm --version)" = "${NPM_VERSION}"; \
    EXPECTED_NODE_VERSION="v${NODE_VERSION}" node -e 'const assert = require("node:assert/strict"); assert.equal(process.version, process.env.EXPECTED_NODE_VERSION); console.log(`Node.js ${process.version} execution passed`)'; \
    smoke_dir="$(mktemp -d)"; \
    mkdir "$smoke_dir/smoke"; \
    cd "$smoke_dir/smoke"; \
    npm init --yes >/dev/null; \
    npm pkg set scripts.smoke='node -e "console.log(\"npm execution passed\")"'; \
    npm run --silent smoke; \
    rm -rf "$smoke_dir"


# ---------------------------------------------------------------------------
# Functional smoke tests
# ---------------------------------------------------------------------------

RUN OPENAI_API_KEY=build-smoke-placeholder python - <<'PY'
from pathlib import Path
import subprocess

import numpy as np

# High-level imports
import aiohttp
import openai
import pydantic_settings
import qdrant_client
import requests
import sentence_transformers
import transformers
import uvicorn
import FlagEmbedding

from docling.document_converter import DocumentConverter
from marker.converters.pdf import PdfConverter

assert DocumentConverter is not None
assert PdfConverter is not None


# PyTorch CPU
import torch
import torchvision

assert torch.__version__ == "2.9.0+cpu"
assert torch.version.cuda is None
assert not torch.cuda.is_available()
assert torchvision.__version__.startswith("0.24.0")

x = torch.tensor([1.0, 2.0])
assert torch.equal(x + 1, torch.tensor([2.0, 3.0]))


# Pyserini -> JNI -> Java 21
from pyserini.pyclass import autoclass

JSystem = autoclass("java.lang.System")
java_version = str(JSystem.getProperty("java.version"))
assert java_version.startswith("21."), java_version

from pyserini.search.lucene import LuceneSearcher
assert LuceneSearcher is not None


# Sparse retrieval
import bm25s
from rank_bm25 import BM25Okapi

corpus = [
    "alpha beta retrieval",
    "gamma delta indexing",
    "epsilon zeta ranking",
]

corpus_tokens = bm25s.tokenize(corpus)

retriever = bm25s.BM25()
retriever.index(corpus_tokens, show_progress=False)

query_tokens = bm25s.tokenize(["alpha retrieval"])

results, scores = retriever.retrieve(
    query_tokens,
    k=1,
    show_progress=False,
)

assert int(results[0][0]) == 0

ranker = BM25Okapi([doc.split() for doc in corpus])
rank_scores = ranker.get_scores(["alpha", "retrieval"])
assert int(np.argmax(rank_scores)) == 0


# FAISS CPU + hnswlib
import faiss
import hnswlib

assert faiss.__version__ == "1.15.0"

vectors = np.asarray(
    [
        [0.0, 0.0],
        [1.0, 1.0],
    ],
    dtype="float32",
)

query = np.asarray([[0.0, 0.0]], dtype="float32")

faiss_index = faiss.IndexFlatL2(2)
faiss_index.add(vectors)

distances, labels = faiss_index.search(query, 1)
assert int(labels[0][0]) == 0

hnsw_index = hnswlib.Index(space="l2", dim=2)
hnsw_index.init_index(
    max_elements=2,
    ef_construction=50,
    M=8,
)
hnsw_index.add_items(vectors, np.asarray([1, 2]))

labels, distances = hnsw_index.knn_query(query, k=1)
assert int(labels[0][0]) == 1


# Generate local video
video_path = "/tmp/runtime-smoke.mp4"

subprocess.run(
    [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "lavfi",
        "-i", "testsrc2=size=64x64:rate=2",
        "-t", "1",
        "-an",
        "-c:v", "mpeg4",
        "-pix_fmt", "yuv420p",
        "-y",
        video_path,
    ],
    check=True,
)

assert Path(video_path).stat().st_size > 0


# PyAV
import av

container = av.open(video_path)
try:
    frame = next(container.decode(video=0))
    assert frame.width == 64
    assert frame.height == 64
finally:
    container.close()


# TorchCodec
from torchcodec.decoders import VideoDecoder

decoder = VideoDecoder(video_path, device="cpu")
frame = decoder[0]

assert frame.dtype == torch.uint8
assert tuple(frame.shape) == (3, 64, 64)
assert frame.device.type == "cpu"


# imageio + imageio-ffmpeg
import imageio.v2 as imageio
import imageio_ffmpeg

reader = imageio.get_reader(video_path, format="ffmpeg")

try:
    frame = reader.get_data(0)
    assert frame.shape == (64, 64, 3)
finally:
    reader.close()

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

subprocess.run(
    [ffmpeg_exe, "-version"],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


# CairoSVG -> PDF
import cairosvg

svg = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
  <rect width="64" height="64" fill="white"/>
  <circle cx="32" cy="32" r="16" fill="black"/>
</svg>
"""

pdf_bytes = cairosvg.svg2pdf(bytestring=svg)
assert pdf_bytes.startswith(b"%PDF")


# pypdfium2
import pypdfium2 as pdfium
from PIL import Image

pdf = pdfium.PdfDocument(pdf_bytes)
assert len(pdf) == 1

page = pdf[0]
bitmap = page.render(scale=1)
image = bitmap.to_pil()

assert isinstance(image, Image.Image)


# pdf2image -> Poppler
from pdf2image import convert_from_bytes

images = convert_from_bytes(
    pdf_bytes,
    first_page=1,
    last_page=1,
)

assert len(images) == 1
assert isinstance(images[0], Image.Image)


# FastAPI + multipart
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/_smoke/upload")
async def smoke_upload(file: UploadFile = File(...)):
    return {"filename": file.filename}

assert app is not None


# tiktoken
import tiktoken

encoding = tiktoken.Encoding(
    name="smoke",
    pat_str=r".",
    mergeable_ranks={
        bytes([i]): i
        for i in range(256)
    },
    special_tokens={},
)

text = "smoke test"
assert encoding.decode(encoding.encode(text)) == text


Path(video_path).unlink(missing_ok=True)

print(
    "CPU search / FAISS 1.15.0 / indexing / Java / "
    "video / PDF / SVG / service runtime checks passed"
)
PY


# Make Conda-provided C/C++ runtime libraries available in fresh containers.
# Some Conda packages, including FAISS, require a newer libstdc++ than the
# one shipped by the slim Debian base image.
ENV LD_LIBRARY_PATH=/opt/conda/lib:/opt/java/openjdk/lib


CMD ["sleep", "infinity"]
