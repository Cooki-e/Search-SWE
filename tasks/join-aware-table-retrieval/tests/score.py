"""Public deterministic scoring; the verifier uses its own protected copy."""
import argparse
import gzip
import json
from pathlib import Path


def load_catalog(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def edge_key(e):
    return tuple(sorted(((e['left_table'], e['left_column']),
                         (e['right_table'], e['right_column']))))


def lookup(catalog):
    return ({t['table_id']: {c['column_id'] for c in t['columns']} for t in catalog['tables']},
            {edge_key(e) for e in catalog['joins']})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key')
        result[key] = value
    return result


def parse_json(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))


def score_one(prediction, gold, catalog_lookup, query_id=None):
    result = {'valid': False, 'table_success': 0, 'joint_success': 0}
    try:
        tables, public_edges = catalog_lookup
        if not isinstance(prediction, dict) or set(prediction) != {'query_id', 'table_ids', 'joins'}:
            raise ValueError('Expected query_id, table_ids and joins')
        if prediction['query_id'] != (gold['query_id'] if query_id is None else query_id):
            raise ValueError('Query ID mismatch')
        pt = prediction['table_ids']
        if not isinstance(pt, list) or len(pt) != 5 or not all(isinstance(t, str) for t in pt):
            raise ValueError('Exactly five table IDs required')
        if len(set(pt)) != 5 or any(t not in tables for t in pt):
            raise ValueError('Unknown or duplicate table ID')
        joins = prediction['joins']
        if not isinstance(joins, list) or len(joins) > 6:
            raise ValueError('At most six joins required')
        pe = set()
        for e in joins:
            if not isinstance(e, dict) or set(e) != {'left_table', 'left_column', 'right_table', 'right_column'}:
                raise ValueError('Invalid join object')
            if not all(isinstance(v, str) for v in e.values()):
                raise ValueError('Join IDs must be strings')
            k = edge_key(e)
            if k in pe or k not in public_edges:
                raise ValueError('Unknown or duplicate join')
            if any(t not in pt or c not in tables[t] for t, c in k):
                raise ValueError('Join endpoint outside returned tables or columns')
            pe.add(k)
        pt = set(pt)
        result['valid'] = True
        for g in gold['acceptable_plans']:
            table_ok = set(g['table_ids']) <= pt
            result['table_success'] |= int(table_ok)
            result['joint_success'] |= int(table_ok and {edge_key(e) for e in g['joins']} <= pe)
    except (TypeError, KeyError, ValueError) as error:
        result['error'] = str(error)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--corpus', required=True)
    p.add_argument('--labels', required=True)
    p.add_argument('--predictions', required=True)
    args = p.parse_args()
    catalog_lookup = lookup(load_catalog(args.corpus))
    gold = [json.loads(line) for line in Path(args.labels).read_text().splitlines()]
    predictions, duplicates = {}, set()
    for line in Path(args.predictions).read_text().splitlines():
        try:
            row = parse_json(line)
            qid = row['query_id']
            if qid in predictions:
                duplicates.add(qid)
            predictions[qid] = row
        except (ValueError, TypeError, KeyError):
            continue
    rows = [score_one(None if g['query_id'] in duplicates else predictions.get(g['query_id']),
                      g, catalog_lookup) for g in gold]
    print(json.dumps({'n': len(rows), 'reward': sum(r['joint_success'] for r in rows) / len(rows),
                      'table_success_rate': sum(r['table_success'] for r in rows) / len(rows),
                      'valid_fraction': sum(r['valid'] for r in rows) / len(rows)}, indent=2))


if __name__ == '__main__':
    main()
