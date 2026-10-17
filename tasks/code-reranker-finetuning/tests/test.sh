#!/usr/bin/env bash
set -u

reward_dir=/logs/verifier
install -d -m 0700 "$reward_dir" "$reward_dir/.private"
printf '0\n' > "$reward_dir/reward.txt"
printf '{"reward": 0.0}\n' > "$reward_dir/reward.json"
rm -f "$reward_dir/.private/first_stage_retrieval.jsonl" "$reward_dir/report.json"

# The only submitted artifact is a checkpoint: no submitted scripts run here.
# Never pass verifier credentials to submission-owned processes.
if ! /usr/bin/timeout --signal=TERM --kill-after=10s 2700s \
    /opt/conda/bin/python /tests/first_stage.py \
    >"$reward_dir/first_stage.log" 2>&1; then
    echo 'local first-stage retrieval failed; reward remains zero' >&2
    exit 1
fi
if ! /usr/bin/timeout --signal=TERM --kill-after=10s 7200s \
    /opt/conda/bin/python /tests/grader.py \
    >"$reward_dir/grader.log" 2>&1; then
    echo 'reranker evaluation failed; reward remains zero' >&2
    exit 1
fi
/opt/conda/bin/python - <<'PY'
import json
import math
from pathlib import Path

root = Path('/logs/verifier')
report = json.loads((root / 'report.json').read_text())
reward = report.get('reward')
if not report.get('valid') or isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(reward) or not 0 <= reward <= 1:
    raise SystemExit('invalid reranker evaluation report')
(root / 'reward.txt').write_text(f'{reward:.10f}\n')
(root / 'reward.json').write_text(json.dumps({'reward': reward}) + '\n')
PY
