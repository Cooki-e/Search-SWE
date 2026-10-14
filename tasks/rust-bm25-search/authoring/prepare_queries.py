#!/usr/bin/env python3
"""Restore verifier-only dev inputs from immutable, checksum-pinned sources."""

import hashlib
import json
import urllib.request
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
REVISION = "8f1bc80988c2483d9519bc2519862b54ab730986"
BASE = f"https://raw.githubusercontent.com/castorini/anserini-tools/{REVISION}/"
SOURCES = {
    "topics/topics.msmarco-passage.dev-subset.txt":
        "f4f71fa87b6be4fb968cca2b8f8554c4ebd003e6c3488af3ac1cc5629c3de189",
    "qrels/qrels.msmarco-passage.dev-subset.txt":
        "34ef51a24e049b3dd19b0a448b764f26b0def22ec42f421ecba2db91f82e7042",
}


def main():
    out = TASK / "tests/data"
    out.mkdir(exist_ok=True)
    records = []
    for filename, expected in SOURCES.items():
        with urllib.request.urlopen(BASE + filename, timeout=60) as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Source checksum mismatch: {filename}")
        if filename.startswith("topics/"):
            queries = [dict(zip(("query_id", "text"), line.split("\t", 1)))
                       for line in data.decode().splitlines()]
            if len(queries) != 6980 or len({q["query_id"] for q in queries}) != 6980:
                raise ValueError("Expected exactly 6,980 unique dev queries")
            target = out / "dev.queries.jsonl"
            target.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queries))
        else:
            target = out / "dev.qrels.tsv"
            target.write_bytes(data)
        records.append({"url": BASE + filename, "source_sha256": expected,
                        "path": target.name, "size_bytes": target.stat().st_size,
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (out / "sources.json").write_text(json.dumps({"files": records}, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
