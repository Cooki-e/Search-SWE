#!/usr/bin/env bash
set -euo pipefail

install -d -o root -g root -m 0700 /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
printf '{"reward":0}\n' > /logs/verifier/reward.json

cleanup() {
    /usr/bin/pkill -TERM -u submission 2>/dev/null || true
    sleep 0.1
    /usr/bin/pkill -KILL -u submission 2>/dev/null || true
}
abort() {
    printf '0\n' > /logs/verifier/reward.txt
    printf '{"reward":0}\n' > /logs/verifier/reward.json
    exit 1
}
trap cleanup EXIT
trap abort TERM INT HUP

test -d /app && test ! -L /app
chown -R --no-dereference root:submission /app
find /app -type d -exec chmod 0550 {} +
find /app -type f -perm /111 -exec chmod 0550 {} +
find /app -type f ! -perm /111 -exec chmod 0440 {} +
chmod 0700 /tests
if [[ -d /logs/agent && ! -L /logs/agent ]]; then
    chown root:root /logs/agent
    chmod 0700 /logs/agent
fi
# Each service run gets fresh scratch space. Shared directories cannot preserve
# hidden-query results between the independently timed service instances.
for directory in /tmp /var/tmp /run/lock /home/submission /dev/shm /dev/mqueue; do
    if [[ -d "$directory" && ! -L "$directory" ]]; then
        chown root:root "$directory"
        chmod 0755 "$directory"
    fi
done

/usr/bin/timeout --signal=TERM --kill-after=5s 2300s \
    /opt/conda/bin/python /tests/grader.py || abort
