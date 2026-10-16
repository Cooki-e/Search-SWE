#!/usr/bin/env bash
set -eu
install -d -o root -g root -m 0700 /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
printf '{"reward":0,"line_f1":0}\n' > /logs/verifier/reward.json
cleanup() {
    /usr/bin/pkill -KILL -u 10001 2>/dev/null || true
}
interrupted() {
    printf '0\n' > /logs/verifier/reward.txt
    printf '{"reward":0,"line_f1":0}\n' > /logs/verifier/reward.json
    exit 143
}
trap cleanup EXIT
trap interrupted TERM INT HUP
/usr/bin/timeout --signal=TERM --kill-after=10s 7500s \
    /opt/conda/bin/python -B /tests/grader.py
