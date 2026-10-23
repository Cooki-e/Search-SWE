#!/usr/bin/env python3
"""Keep runner diagnostics in Harbor's exported verifier directory."""
from pathlib import Path
import shutil
import stat

SOURCE = Path('/logs/artifacts/sparse-retrieval-pruning-eval')
DESTINATION = Path('/logs/verifier/runner-artifacts')


def collect(source=SOURCE, destination=DESTINATION):
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    paths = [p for p in source.iterdir() if p.suffix in ('.json', '.log')]
    for directory in source.glob('round-*'):
        if stat.S_ISDIR(directory.lstat().st_mode):
            result = directory / 'results.jsonl'
            if result.exists():
                paths.append(result)
    for path in sorted(paths):
        # Never follow submission-created symlinks or copy indexes/scratch.
        if not stat.S_ISREG(path.lstat().st_mode):
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(path, target)
        target.chmod(0o600)


if __name__ == '__main__':
    collect()
