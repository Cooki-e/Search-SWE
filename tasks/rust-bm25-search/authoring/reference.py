#!/usr/bin/env python3
"""Author entry point for the verifier-owned reference runner."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "tests/reference.py"), run_name="__main__")
