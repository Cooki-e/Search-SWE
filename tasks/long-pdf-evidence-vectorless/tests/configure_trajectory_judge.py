#!/usr/bin/env python3
"""Validate verifier-only settings and stage the trajectory-judge rubric."""

import argparse
import os
from pathlib import Path
import shutil


def configure(template, output):
    names = ("OPENAI_BASE_URL", "OPENAI_API_KEY")
    values = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ValueError("missing trajectory judge settings: " + ", ".join(missing))
    base = values["OPENAI_BASE_URL"].rstrip("/")
    if base != "https://openrouter.ai/api/v1":
        raise ValueError("judge endpoint must be https://openrouter.ai/api/v1")
    output.mkdir(parents=True, exist_ok=True)
    criterion = output / "jailbreak_judge"
    criterion.mkdir(exist_ok=True)
    shutil.copyfile(template, criterion / "codex.toml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    configure(args.template, args.output)
