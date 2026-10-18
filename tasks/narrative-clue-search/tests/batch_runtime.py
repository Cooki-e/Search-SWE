"""Recover only fully written JSON rows after a terminated query call."""

import json, stat
from pathlib import Path


def completed_rows(path):
    p = Path(path)
    try:
        if not stat.S_ISREG(p.lstat().st_mode):
            return []
    except FileNotFoundError:
        return []
    rows = []
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def independent_budget(total, batches, index):
    if not batches or not 0 <= index < len(batches):
        raise ValueError("Invalid batch plan")
    return float(total) / len(batches)
