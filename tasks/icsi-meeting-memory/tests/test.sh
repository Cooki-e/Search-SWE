#!/usr/bin/env bash
set -uo pipefail
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1 LITELLM_LOCAL_MODEL_COST_MAP=True
umask 077
pkill -KILL -u 10001 2>/dev/null || true
pkill -KILL -u 10002 2>/dev/null || true
install -d -o root -g root -m 0700 /logs/agent /logs/verifier
chown -R root:root /tests
chmod -R go-rwx /tests
cd /tests
printf '0\n' > /logs/verifier/reward.txt
printf '{"reward":0}\n' > /logs/verifier/reward.json
rm -f /logs/verifier/rewardkit.json /logs/verifier/reward-details.json /logs/verifier/gate-status.json
cleanup() { pkill -KILL -u 10001 2>/dev/null || true; pkill -KILL -u 10002 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 143' INT TERM HUP
timeout --signal=TERM --kill-after=10 3600 /opt/conda/bin/python -I /tests/grader.py
grader_status=$?
cleanup
judge_status=78
if [[ -n "${OPENAI_API_KEY:-}" && "${OPENAI_BASE_URL%/}" == 'https://openrouter.ai/api/v1' && -f /logs/agent/trajectory.json && ! -L /logs/agent/trajectory.json ]]; then
 install -d -o root -g audit -m 0750 /audit /audit/config /audit/config/jailbreak_judge
 install -d -o audit -g audit -m 0700 /audit/output /home/audit/tmp
 cp -a /app /audit/submission
 chown -R root:audit /audit/submission
 find /audit/submission -type d -exec chmod 0550 {} +
 find /audit/submission -type f -exec chmod 0440 {} +
 install -o root -g audit -m 0440 /logs/agent/trajectory.json /audit/trajectory.json
 install -o root -g audit -m 0440 /tests/jailbreak_judge/codex.toml /audit/config/jailbreak_judge/codex.toml
 timeout --signal=TERM --kill-after=10 1500 /opt/conda/bin/python /tests/run_audit.py --runner /tests/rewardkit_deepseek.py --judge deepseek-codex --model deepseek/deepseek-v4.1-flash > /logs/verifier/judge.stdout 2> /logs/verifier/judge.stderr
 judge_status=$?
 if [[ -f /audit/output/reward.json ]]; then install -o root -g root -m 0600 /audit/output/reward.json /logs/verifier/rewardkit.json; fi
 if [[ -f /audit/output/reward-details.json ]]; then install -o root -g root -m 0600 /audit/output/reward-details.json /logs/verifier/reward-details.json; fi
fi
cleanup
/opt/conda/bin/python /tests/collect_audit_logs.py
SEARCH_SWE_JUDGE_STATUS="$judge_status" /opt/conda/bin/python -I /tests/finalize_reward.py
final_status=$?
if (( grader_status || final_status )); then exit 1; fi
