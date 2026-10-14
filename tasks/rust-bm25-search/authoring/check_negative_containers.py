#!/usr/bin/env python3
"""Exercise fail-closed grading in fresh disposable verifier containers."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
BAD_PROTOCOL = r'''
use std::{env,fs,io::{self,BufRead}};
fn main() {
    let args: Vec<String> = env::args().collect();
    if args[1]=="index" {
        let p=args.iter().position(|x|x=="--index").unwrap();
        fs::write(format!("{}/artifact",args[p+1]),b"invalid fixture").unwrap();
    } else {
        for _ in io::stdin().lock().lines() {println!("not a JSON response");}
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="search-swe-local:rust-bm25-verifier")
    parser.add_argument("--sudo", action="store_true")
    parser.add_argument("--case", action="append", choices=["missing", "malformed-manifest", "command-failure", "malformed-response"])
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    docker = ["sudo", "-n", "docker"] if args.sudo else ["docker"]
    records = []
    for case in args.case or ["missing", "malformed-manifest", "command-failure", "malformed-response"]:
        source, logs = root / case / "source", root / case / "logs"
        logs.mkdir(parents=True)
        if case == "missing":
            source.mkdir()
        else:
            shutil.copytree(TASK / "environment/starter", source)
            if case == "malformed-manifest":
                (source / "Cargo.toml").write_text("package = []\n")
            if case == "malformed-response":
                (source / "src/main.rs").write_text(BAD_PROTOCOL)
        command = [*docker, "run", "--rm", "--network", "none", "--cpus", "4",
                   "--memory", "16g", "--memory-swap", "16g", "--pids-limit", "256",
                   "-v", f"{source}:/app/submission:ro",
                   "-v", f"{TASK / 'data'}:/task/data:ro",
                   "-v", f"{logs}:/logs/verifier", args.image, "bash", "/tests/test.sh"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
        (root / case / "container.log").write_text(completed.stdout + completed.stderr)
        report = json.loads((logs / "report.json").read_text())
        assert completed.returncode == 0, (case, completed.returncode)
        assert report["status"] == "invalid_submission", (case, report)
        assert float((logs / "reward.txt").read_text()) == 0, (case, report)
        records.append({"case": case, "status": report["status"], "error": report["error"], "reward": 0})
        print(json.dumps(records[-1]), flush=True)
    (root / "summary.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
