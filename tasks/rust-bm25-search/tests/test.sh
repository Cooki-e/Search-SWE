#!/usr/bin/env bash
set -euo pipefail

reward_dir=/logs/verifier
mkdir -p "$reward_dir"
printf '0\n' > "$reward_dir/reward.txt"
chmod 700 "$reward_dir"
# Harbor may share a network namespace with its egress-control sidecar.
# Docker forbids an explicit hostname/extra_hosts in that mode. Resolve the
# inherited hostname locally so Lucene can initialize without a DNS request.
/opt/conda/bin/python - <<'PY'
import socket
from pathlib import Path

hostname = socket.gethostname()
hosts = Path("/etc/hosts")
aliases = {alias for line in hosts.read_text().splitlines()
           for alias in line.split("#", 1)[0].split()[1:]}
if hostname not in aliases:
    with hosts.open("a") as stream:
        stream.write(f"\n127.0.0.1 {hostname}\n")
PY
exec /opt/conda/bin/python /tests/grader.py
