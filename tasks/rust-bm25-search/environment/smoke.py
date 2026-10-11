#!/usr/bin/env python3
"""Exercise the public CLI on three synthetic passages, without dev labels."""

import argparse
import gzip
import json
import math
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    binary = str(args.binary.resolve(strict=True))
    with tempfile.TemporaryDirectory(prefix="bm25-smoke-") as directory:
        root = Path(directory)
        corpus, index = root / "corpus.jsonl.gz", root / "index"
        index.mkdir()
        passages = ["bronze bronze alpha", "silver silver beta", "gold gold gamma"]
        with gzip.open(corpus, "wt", encoding="utf-8") as stream:
            for i, passage in enumerate(passages):
                stream.write(json.dumps({"docid": str(i), "text": passage, "title": "metadata only"}) + "\n")
        subprocess.run([binary, "index", "--corpus", str(corpus), "--index", str(index),
                        "--threads", "4"], check=True, timeout=60)
        queries = [{"query_id": "toy-a", "text": "bronze"}, {"query_id": "toy-b", "text": "gold"}]
        result = subprocess.run([binary, "search", "--index", str(index), "--threads", "4"],
                                input="".join(json.dumps(q) + "\n" for q in queries),
                                text=True, capture_output=True, check=True, timeout=30)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        assert len(rows) == 2, "Expected exactly one response per query"
        for row, query, expected in zip(rows, queries, ["0", "2"]):
            assert row["query_id"] == query["query_id"]
            assert row["results"] and row["results"][0]["doc_id"] == expected
            ids = [hit["doc_id"] for hit in row["results"]]
            scores = [hit["score"] for hit in row["results"]]
            assert len(ids) <= 10 and len(set(ids)) == len(ids) and set(ids) <= {"0", "1", "2"}
            assert all(not isinstance(x, bool) and math.isfinite(x) for x in scores)
            assert scores == sorted(scores, reverse=True)
        print("Public synthetic CLI check passed; this does not measure full-dev MRR.")


if __name__ == "__main__":
    main()
