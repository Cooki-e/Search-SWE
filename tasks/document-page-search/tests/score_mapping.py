"""Convert the task's raw quality to a fixed piecewise-normalized reward."""

import math

BASELINE_RAW = 0.5362634643282924
BASELINE_SCORE = 20


def normalize_score(raw):
    """Map 0, the reference quality, and 1 to 0, the score anchor, and 1."""
    if type(raw) not in (int, float):
        raise ValueError("Raw quality must be a finite number in [0, 1]")
    try:
        valid = math.isfinite(raw) and 0 <= raw <= 1
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("Raw quality must be a finite number in [0, 1]")
    anchor = BASELINE_SCORE / 100
    if raw <= BASELINE_RAW:
        return anchor * (raw / BASELINE_RAW)
    return anchor + (1 - anchor) * ((raw - BASELINE_RAW) / (1 - BASELINE_RAW))
