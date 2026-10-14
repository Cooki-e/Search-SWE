#!/usr/bin/env python3
"""Run inside a disposable verifier image; never execute on the host."""

import json
import os
import subprocess
import sys
from pathlib import Path

PROBE = r'''
use std::fs::{self,OpenOptions};
fn main() {
    assert!(fs::read("/tests/data/dev.qrels.tsv").is_err(), "hidden labels readable");
    assert!(fs::write("/logs/verifier/reward.txt", b"1").is_err(), "reward writable");
    if std::env::args().nth(1).unwrap()=="search" {
        assert_eq!(fs::read("/work/index/probe").unwrap(), b"index");
        assert!(fs::read("/task/data/corpus.jsonl.gz").is_err(), "raw corpus readable in search");
        assert!(fs::read("/tmp/outside-index").is_err(), "outside cache readable");
        assert!(OpenOptions::new().write(true).truncate(true).open("/work/index/probe").is_err(), "index truncatable");
        assert!(fs::write("/tmp/new-cache", b"cached").is_err(), "persistent cache writable");
    } else {
        assert!(fs::read("/task/data/corpus.jsonl.gz").is_ok(), "corpus not readable when indexing");
        fs::write("/work/index/probe",b"index").unwrap();
    }
    println!("isolation probe passed");
}
'''


def main():
    if os.geteuid() != 0 or not Path("/.dockerenv").exists():
        raise RuntimeError("Use a fresh disposable verifier container")
    sys.path.insert(0, "/tests")
    from grader import ENV, kill_submission_processes
    Path("/work").mkdir(mode=0o711)
    for name in ["index", "tmp"]:
        path = Path("/work") / name
        path.mkdir()
        os.chown(path, 10001, 10001)
    Path("/logs/verifier").mkdir(parents=True, mode=0o700)
    Path("/logs/verifier/reward.txt").write_text("0\n")
    Path("/task/data").mkdir(parents=True, exist_ok=True)
    Path("/task/data/corpus.jsonl.gz").write_bytes(b"fixture corpus")
    Path("/tmp/outside-index").write_text("cached state")
    Path("/tmp/probe.rs").write_text(PROBE)
    subprocess.run(["/opt/rust/bin/rustc", "/tmp/probe.rs", "-o", "/work/bm25-search"], check=True)
    os.chmod("/work/bm25-search", 0o555)
    for mode in ["index", "search"]:
        if mode == "search":
            os.chown("/work/index", 0, 0)
            os.chown("/work/index/probe", 0, 0)
            os.chmod("/work/index", 0o555)
            os.chmod("/work/index/probe", 0o444)
        try:
            subprocess.run([sys.executable, "/tests/isolate.py", mode, "/work/bm25-search", mode],
                           check=True, timeout=20, env=ENV)
        finally:
            kill_submission_processes()
    assert Path("/logs/verifier/reward.txt").read_text() == "0\n"
    print(json.dumps({"index_and_search_isolation": "passed", "reward_unchanged": True}))


if __name__ == "__main__":
    main()
