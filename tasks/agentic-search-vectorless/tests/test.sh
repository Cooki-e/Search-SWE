#!/usr/bin/env bash
set -u

install -d -o root -g root -m 0711 /logs/verifier
install -d -o root -g root -m 0700 /logs/verifier/.private
if [[ -d /logs/agent && ! -L /logs/agent ]]; then
    chown root:root /logs/agent
    chmod 0700 /logs/agent
fi
printf '0\n' > /logs/verifier/reward.txt
printf '{"gold_recall_at_5": 0.0, "jailbreak_judge": 0.0, "reward": 0.0}\n' \
    > /logs/verifier/reward.json
chmod 0600 /logs/verifier/reward.txt /logs/verifier/reward.json

cleanup_submission_processes() {
    /usr/bin/pkill -TERM -u 65534 2>/dev/null || true
    /usr/bin/pkill -KILL -u 65534 2>/dev/null || true
}
trap cleanup_submission_processes EXIT
trap 'exit 143' TERM INT HUP

/opt/conda/bin/python /tests/trajectory_gate.py
