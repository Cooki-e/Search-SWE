#!/usr/bin/env python3
"""Convert pinned passage text to Lucene JSONL without adding Tevatron titles."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from pathlib import Path

CORPUS_DOCUMENTS = 8_841_823
CORPUS_SHA256 = "634543cee77a992613bbf32d0aa4863659dffd064c405f062454400aa80aea3f"


def file_metadata(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"name": path.name, "size_bytes": path.stat().st_size, "sha256": digest}


def prepare(corpus: Path, destination: Path, *, smoke_limit: int | None = None) -> dict:
    with corpus.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != CORPUS_SHA256:
        raise ValueError("Corpus SHA-256 differs from the pinned MS MARCO input")
    if smoke_limit is not None and not 0 < smoke_limit <= CORPUS_DOCUMENTS:
        raise ValueError("Invalid smoke limit")
    destination.mkdir(parents=True, exist_ok=False)
    expected = smoke_limit or CORPUS_DOCUMENTS
    seen = bytearray(CORPUS_DOCUMENTS)
    started, count, output = time.monotonic(), 0, None
    try:
        with gzip.open(corpus, "rt", encoding="utf-8") as stream:
            for line in stream:
                if smoke_limit is not None and count >= smoke_limit:
                    break
                row = json.loads(line)
                docid, text = row["docid"], row["text"]
                if not isinstance(docid, str) or not docid.isascii() or not docid.isdigit():
                    raise ValueError("Invalid document ID")
                numeric = int(docid)
                if str(numeric) != docid or not 0 <= numeric < CORPUS_DOCUMENTS or seen[numeric]:
                    raise ValueError("Noncanonical, out-of-range, or duplicate document ID")
                if not isinstance(text, str):
                    raise ValueError("Passage text must be a string")
                seen[numeric] = 1
                if count % 1_000_000 == 0:
                    if output is not None:
                        output.close()
                    output = (destination / f"part-{count // 1_000_000:02d}.jsonl").open("w", encoding="utf-8")
                # The title in this mirror is additional metadata. BM25's
                # reference and Rust submissions both index only the text.
                output.write(json.dumps({"id": docid, "contents": text}, ensure_ascii=False) + "\n")
                count += 1
                if count % 1_000_000 == 0:
                    print(f"Converted {count:,} passages", flush=True)
    finally:
        if output is not None:
            output.close()
    if count != expected:
        raise ValueError(f"Expected {expected} passages, got {count}")
    if smoke_limit is None and not all(seen):
        raise ValueError("Corpus ID coverage is incomplete")
    metadata = {"schema_version": 1, "corpus_sha256": digest, "document_count": count,
                "scope": "smoke" if smoke_limit else "full",
                "content_field": "text", "title_field_indexed": False,
                "conversion_seconds": time.monotonic() - started,
                "source_files": [file_metadata(path) for path in sorted(destination.glob("*.jsonl"))]}
    # Keep metadata outside the JsonCollection input directory.
    destination.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke-limit", type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.corpus, args.output, smoke_limit=args.smoke_limit), indent=2))


if __name__ == "__main__":
    main()
