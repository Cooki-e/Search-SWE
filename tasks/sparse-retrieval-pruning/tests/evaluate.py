#!/usr/bin/env python3
"""Build once, then measure five protected alternating search rounds."""
import json
import os
from pathlib import Path
import shutil
import stat
import sys

from grader import (grade_rounds, load_corpus_ids, load_jsonl, load_qrels,
                    query_ids, validate_results, ROUND_COUNT, REWARD_METRIC)
from run_with_metrics import run, stop_members

ROOT = Path('/logs/artifacts/sparse-retrieval-pruning-eval')
REPORT = Path('/logs/verifier/report.json')
UID = 10001


def freeze(root, allow_symlinks=False):
    for path in [root, *root.rglob('*')]:
        info = path.lstat()
        if path.is_symlink() and allow_symlinks:
            os.chown(path, 0, 0, follow_symlinks=False)
            continue
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or path.is_symlink():
            raise ValueError(f'unsupported index/source file: {path}')
        os.chown(path, 0, 0)
        path.chmod(0o555 if path.is_dir() or info.st_mode & 0o111 else 0o444)


def private_directory(path):
    path.mkdir(parents=True)
    os.chown(path, UID, UID)
    path.chmod(0o700)


def main():
    os.umask(0o077)
    for parent in (Path('/logs'), Path('/logs/artifacts')):
        parent.mkdir(exist_ok=True)
        parent.chmod(0o711)
    ROOT.mkdir(parents=True, exist_ok=True)
    ROOT.chmod(0o711)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.chmod(0o700)
    rounds = []
    try:
        # Each verifier gets fresh artifact storage. Refuse stale runs.
        if list(ROOT.iterdir()):
            raise ValueError('evaluation artifact directory must be empty')
        freeze(Path('/app'), allow_symlinks=True)
        cpu = min(os.sched_getaffinity(0))
        inputs = Path('/tests/data')
        ids = query_ids(inputs / 'hidden_queries.jsonl')
        valid_docs = load_corpus_ids(inputs / 'corpus_ids.txt')
        qrels = load_qrels(inputs / 'qrels.tsv')
        reference = validate_results(load_jsonl(inputs / 'reference_top100.jsonl'), ids, valid_docs)
        indexes = {}
        roots = {'candidate': Path('/app'), 'starter': Path('/baseline-starter')}
        for side in ('candidate', 'starter'):
            source = roots[side]
            area = ROOT / (side + '-build-area')
            index = area / 'index'
            scratch = ROOT / (side + '-build-scratch')
            private_directory(area)
            private_directory(scratch)
            command = [str(source / 'build.sh'), '--corpus', '/task/data/corpus.jsonl', '--index-dir', str(index)]
            run(command, metrics_path=ROOT / (side + '-build.metrics.json'),
                log_prefix=ROOT / (side + '-build'), timeout=3600 if side == 'candidate' else 1800,
                readable=[source, Path('/task/data')], writable=[area, scratch], scratch=scratch, cpu=cpu)
            if not any(index.iterdir()):
                raise ValueError(f'{side} produced an empty index')
            if set(area.iterdir()) != {index}:
                raise ValueError("persistent build state outside --index-dir")
            freeze(area)
            shutil.rmtree(scratch)
            indexes[side] = index
        for number in range(1, ROUND_COUNT + 1):
            order = ['starter', 'candidate'] if number % 2 else ['candidate', 'starter']
            row = {'round': number, 'order': order}
            for side in order:
                label = f'round-{number}-{side}'
                output_dir = ROOT / label
                scratch = ROOT / (label + '-scratch')
                private_directory(output_dir)
                private_directory(scratch)
                result = output_dir / 'results.jsonl'
                metrics = ROOT / (label + '.metrics.json')
                command = [str(roots[side] / 'run.sh'), '--index-dir', str(indexes[side]),
                           '--queries', str(inputs / 'hidden_queries.jsonl'), '--output', str(result)]
                run(command, metrics_path=metrics, log_prefix=ROOT / label, timeout=900,
                    readable=[roots[side], indexes[side], inputs / 'hidden_queries.jsonl'],
                    writable=[output_dir, scratch], scratch=scratch, cpu=cpu)
                freeze(output_dir)
                output_dir.chmod(0o700)
                shutil.rmtree(scratch)
                # Validate every round immediately; no selected fastest/best output.
                validate_results(load_jsonl(result), ids, valid_docs)
                row[side] = {'results': str(result), 'metrics': str(metrics)}
            rounds.append(row)
            (ROOT / 'rounds.json').write_text(json.dumps(rounds, indent=2) + '\n')
        report = grade_rounds(rounds, ids, valid_docs, qrels, reference)
        status = 0
    except Exception as exc:
        report = {'status': 'invalid', 'reward_metric': REWARD_METRIC, 'reward': 0.0,
                  'score': 0.0, 'error': f'{type(exc).__name__}: {exc}', 'completed_rounds': rounds}
        status = 1
    finally:
        stop_members()
    REPORT.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rounds'}, indent=2, allow_nan=False))
    return status


if __name__ == '__main__':
    sys.exit(main())
