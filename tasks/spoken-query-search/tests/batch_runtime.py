"""Read completed JSON objects without discarding other rows on malformed output."""

import json, math, stat
from pathlib import Path


class _InvalidNumber(ValueError):
    pass


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise _InvalidNumber("Non-finite JSON number")
    return value


def _reject_constant(text):
    raise _InvalidNumber("Non-standard JSON number: " + text)


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
                row = json.loads(
                    line, parse_float=_finite_float, parse_constant=_reject_constant
                )
            except _InvalidNumber:
                # Preserve identity for duplicate/unknown-ID checks, but retain
                # none of the malformed numeric payload in diagnostic output.
                try:
                    identity = json.loads(line)
                except ValueError:
                    continue
                if isinstance(identity, dict) and isinstance(
                    identity.get("query_id"), str
                ):
                    rows.append({"query_id": identity["query_id"]})
                continue
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def independent_budget(total, batches, index):
    if not batches or not 0 <= index < len(batches):
        raise ValueError("Invalid batch plan")
    return float(total) / len(batches)
