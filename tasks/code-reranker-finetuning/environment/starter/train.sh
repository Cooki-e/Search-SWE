#!/usr/bin/env bash
set -euo pipefail
export TOKENIZERS_PARALLELISM=false
exec /opt/conda/bin/python "$(dirname "$(readlink -f "$0")")/train.py" "$@"
