#!/usr/bin/env bash
set -eu
mkdir -p /logs/verifier
chmod 755 /logs
chmod 700 /logs/verifier
printf "0\n" > /logs/verifier/reward.txt
exec /opt/conda/bin/python -I /tests/grade.py
