"""Deterministic scoring of physical source lines within one repository snapshot."""
import json
import math
import posixpath

MAX_REGIONS = 5
MAX_LINES = 500


def parse_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Non-finite JSON constant')

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Non-finite JSON number')
        return result

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)


def read_jsonl(path):
    with path.open(encoding='utf-8') as stream:
        return [parse_json(line) for line in stream if line.strip()]


def load_files(path):
    if path.is_symlink() or not path.is_dir():
        raise ValueError('Expected a repository collection directory')
    snapshots = {}
    for snapshot in sorted(path.iterdir()):
        if snapshot.is_symlink() or not snapshot.is_dir():
            raise ValueError('Expected a snapshot directory')
        files = snapshots[snapshot.name] = {}
        for source in sorted(snapshot.rglob('*')):
            if source.is_symlink():
                raise ValueError('Symlink in repository collection')
            if source.is_dir():
                continue
            if not source.is_file():
                raise ValueError('Expected a regular source file')
            raw = source.read_bytes()
            files[source.relative_to(snapshot).as_posix()] = raw.count(b'\n') + int(bool(raw) and not raw.endswith(b'\n'))
    return snapshots


def line_set(regions, files):
    if not isinstance(regions, list) or len(regions) > MAX_REGIONS:
        raise ValueError('Expected at most five regions')
    result = set()
    for region in regions:
        if not isinstance(region, dict) or not {'path', 'start', 'end'} <= region.keys():
            raise ValueError('Malformed source region')
        path = region['path']
        if not isinstance(path, str):
            raise ValueError('Path must be a string')
        path = posixpath.normpath(path)
        if path.startswith('/') or path == '..' or path.startswith('../'):
            raise ValueError('Path is outside the snapshot')
        start, end = region['start'], region['end']
        if type(start) is not int or type(end) is not int:
            raise ValueError('Line numbers must be integers')
        if not 1 <= start <= end <= files.get(path, 0):
            raise ValueError('Unknown path or invalid line range')
        if end - start + 1 > MAX_LINES:
            raise ValueError('More than 500 distinct lines')
        result.update((path, number) for number in range(start, end + 1))
        if len(result) > MAX_LINES:
            raise ValueError('More than 500 distinct lines')
    return result


def score_one(prediction, gold, files, query_id):
    target = line_set(gold, files)
    if not target:
        raise ValueError('Gold must contain source lines')
    try:
        if not isinstance(prediction, dict) or set(prediction) != {'query_id', 'regions'}:
            raise ValueError('Expected query_id and regions')
        if prediction['query_id'] != query_id:
            raise ValueError('Query ID mismatch')
        for region in prediction['regions'] if isinstance(prediction['regions'], list) else []:
            if not isinstance(region, dict) or set(region) != {'path', 'start', 'end'}:
                raise ValueError('Expected path, start and end in each region')
        retrieved = line_set(prediction['regions'], files)
    except ValueError as error:
        return {'valid': False, 'f1': 0., 'precision': 0., 'recall': 0., 'error': str(error)}
    hits = len(retrieved & target)
    return {'valid': True, 'f1': 2 * hits / (len(retrieved) + len(target)),
            'precision': hits / len(retrieved) if retrieved else 0.,
            'recall': hits / len(target), 'hit_lines': hits,
            'predicted_lines': len(retrieved), 'gold_lines': len(target)}
