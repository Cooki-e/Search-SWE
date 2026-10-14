#!/usr/bin/env python3
"""Build and measure the pinned Pyserini BM25 reference in a bounded runtime."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import signal
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK / "tests"))
from benchmark import index_bytes, measure, sha256
from evaluate import evaluate, load_qrels, load_queries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    build = sub.add_parser("build")
    build.add_argument("--collection", type=Path, required=True)
    build.add_argument("--index", type=Path, required=True)
    build.add_argument("--threads", type=int, default=4)
    build.add_argument("--timeout", type=int, default=7200)
    bench = sub.add_parser("measure")
    bench.add_argument("--index", type=Path, required=True)
    bench.add_argument("--queries", type=Path, required=True)
    bench.add_argument("--qrels", type=Path, required=True)
    bench.add_argument("--warmup", type=Path, required=True)
    bench.add_argument("--output", type=Path, required=True)
    bench.add_argument("--document-count", type=int, default=8_841_823)
    bench.add_argument("--cold-samples", type=int, default=5)
    bench.add_argument("--query-timeout", type=float, default=120)
    bench.add_argument("--batch-timeout", type=float, default=3600)
    bench.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if version("pyserini") != "1.4.0":
        parser.error("Run this tool in the task image: pyserini==1.4.0 is required")
    if args.operation == "build":
        if args.index.exists():
            parser.error("Reference index destination must not already exist")
        if args.threads < 1 or args.timeout < 1:
            parser.error("Threads and timeout must be positive")
        metadata = args.collection.with_suffix(".metadata.json")
        if not metadata.is_file():
            parser.error("Run prepare_corpus.py first; conversion metadata is required")
        args.index.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "pyserini.index.lucene", "--collection", "JsonCollection",
                   "--input", str(args.collection), "--index", str(args.index),
                   "--generator", "DefaultLuceneDocumentGenerator", "--threads", str(args.threads)]
        # No --storeRaw, --storePositions or --storeDocvectors: the task returns
        # IDs and scores only, so those features would inflate the reference.
        log = args.index.with_suffix(".build.log")
        started = time.monotonic()
        with log.open("wb") as stream:
            result = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                      start_new_session=True)
            try:
                result.wait(timeout=args.timeout)
            finally:
                try:
                    os.killpg(result.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                result.wait()
        if result.returncode:
            raise RuntimeError(f"Reference indexing failed; inspect {log}")
        report = {"command": command, "build_seconds": time.monotonic() - started,
                  "build_max_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  "index_bytes": index_bytes(args.index), "pyserini_version": "1.4.0",
                  "collection": json.loads(metadata.read_text()),
                  "stored_raw": False, "stored_positions": False, "stored_docvectors": False}
        args.index.with_suffix(".build.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return
    queries, warmup = load_queries(args.queries), load_queries(args.warmup)
    if not args.smoke and (len(queries) != 6980 or args.document_count != 8_841_823):
        parser.error("A full reference must use 6,980 dev queries and 8,841,823 passages")
    build_path = args.index.with_suffix(".build.json")
    if not build_path.is_file():
        parser.error("Reference build provenance is missing")
    build_report = json.loads(build_path.read_text())
    if not args.smoke and build_report["collection"]["scope"] != "full":
        parser.error("A smoke index cannot become a full reference")
    if build_report["collection"]["document_count"] != args.document_count:
        parser.error("Index and evaluation document counts disagree")
    qrels = load_qrels(args.qrels, {q["query_id"] for q in queries})
    metrics, results = measure([sys.executable, str(TASK / "tests/reference_worker.py"),
                                "--index", str(args.index)], queries=queries, warmup=warmup,
                               directory=args.output, document_count=args.document_count,
                               cold_samples=args.cold_samples, timeout=args.query_timeout,
                               batch_timeout=args.batch_timeout)
    report = {**metrics, "schema_version": 1, "scope": "smoke" if args.smoke else "full",
              "reference": {"pyserini": "1.4.0", "k1": .9, "b": .4, "top_k": 10},
              "quality": evaluate(results, queries, qrels, document_count=args.document_count),
              "index_bytes": index_bytes(args.index), "document_count": args.document_count,
              "inputs": {"queries_sha256": sha256(args.queries), "qrels_sha256": sha256(args.qrels),
                         "warmup_sha256": sha256(args.warmup),
                         "corpus_sha256": build_report["collection"]["corpus_sha256"]},
              "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                          "cpu_affinity": sorted(os.sched_getaffinity(0))},
              "reference_build": build_report,
              "scoring_status": "measurement only; production calibration remains separate"}
    (args.output / "reference.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": str(args.output / "reference.json"), "scope": report["scope"],
                      "quality": report["quality"], "warm_seconds": report["warm_seconds"],
                      "index_bytes": report["index_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
