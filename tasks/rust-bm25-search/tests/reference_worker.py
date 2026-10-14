#!/usr/bin/env python3
"""Verifier-owned Pyserini reference; never copied to the agent environment."""

import argparse
import json
import os
import sys
from importlib.metadata import version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True)
    args = parser.parse_args()
    if version("pyserini") != "1.4.0":
        parser.error("This reference requires pyserini==1.4.0")
    # Pyserini 1.4 imports optional encoders while importing LuceneSearcher.
    # Their module constructs an unused OpenAI client. BM25 needs no service or
    # credential; a non-secret sentinel satisfies that constructor offline.
    os.environ["OPENAI_API_KEY"] = "unused-local-bm25-reference"
    from pyserini.search.lucene import LuceneSearcher
    searcher = LuceneSearcher(args.index)
    searcher.set_bm25(0.9, 0.4)
    try:
        for line in sys.stdin:
            query = json.loads(line)
            hits = searcher.search(query["text"], k=10)
            result = {"query_id": query["query_id"], "results": [
                {"doc_id": hit.docid, "score": float(hit.score)} for hit in hits]}
            print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    finally:
        searcher.close()


if __name__ == "__main__":
    main()
