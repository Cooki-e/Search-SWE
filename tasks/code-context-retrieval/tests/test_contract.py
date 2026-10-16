import tempfile
from pathlib import Path
import unittest

from scoring import line_set, load_files, parse_json, score_one


def region(path='a.py', start=1, end=10):
    return {'path': path, 'start': start, 'end': end}


class ScoringContract(unittest.TestCase):
    files = {'a.py': 700, 'b.py': 100}
    gold = [region(end=100)]

    def score(self, regions, qid='q'):
        return score_one({'query_id': qid, 'regions': regions}, self.gold, self.files, 'q')

    def test_full_gold_and_partial_coverage(self):
        self.assertEqual(self.score(self.gold)['f1'], 1.)
        self.assertAlmostEqual(self.score([region(end=1)])['f1'], 2 / 101)
        self.assertAlmostEqual(self.score([region(end=200)])['f1'], 2 / 3)

    def test_overlap_and_path_normalization(self):
        result = self.score([region('./a.py', 1, 60), region('a.py', 40, 100)])
        self.assertEqual(result['predicted_lines'], 100)
        self.assertEqual(result['f1'], 1.)

    def test_file_identity_and_wrong_query_id(self):
        self.assertEqual(self.score([region('b.py', 1, 100)])['f1'], 0.)
        self.assertFalse(self.score(self.gold, qid='wrong')['valid'])

    def test_actual_bounds_and_types(self):
        for r in [region('missing.py'), region('/a.py'), region('../a.py'),
                  region(end=701), region(start=0), region(start=11, end=10),
                  region(start=True), region(end=10.)]:
            with self.subTest(r=r):
                self.assertFalse(self.score([r])['valid'])

    def test_budgets_count_unique_lines(self):
        self.assertTrue(self.score([region(end=500)])['valid'])
        self.assertFalse(self.score([region(end=501)])['valid'])
        self.assertTrue(self.score([region(end=400), region(start=101, end=500)])['valid'])
        self.assertFalse(self.score([region(end=450), region('b.py', 1, 51)])['valid'])
        self.assertFalse(self.score([region()] * 6)['valid'])
        self.assertEqual(self.score([])['f1'], 0.)

    def test_strict_output_schema_and_json(self):
        for text in ['{"query_id":"q","query_id":"r"}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}']:
            with self.assertRaises(ValueError):
                parse_json(text)
        for prediction in [None, [], {}, {'query_id': 'q', 'regions': {}, 'extra': 1},
                           {'query_id': 'q', 'regions': [{**region(), 'score': 1}]}]:
            self.assertFalse(score_one(prediction, self.gold, self.files, 'q')['valid'])

    def test_physical_lines_and_snapshot_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'repos'
            (path / 's1').mkdir(parents=True)
            (path / 's2').mkdir()
            (path / 's1/a.py').write_bytes(b'a\fb\r\nc\n')
            (path / 's2/a.py').write_bytes(b'x')
            files = load_files(path)
            self.assertEqual(files['s1']['a.py'], 2)
            self.assertEqual(files['s2']['a.py'], 1)
            self.assertEqual(len(line_set([region(end=2)], files['s1'])), 2)
            with self.assertRaises(ValueError):
                line_set([region(end=2)], files['s2'])

    def test_symlinks_are_not_corpus_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'repos'
            (path / 's1').mkdir(parents=True)
            (Path(tmp) / 'outside.py').write_bytes(b'x\n')
            (path / 's1/link.py').symlink_to(Path(tmp) / 'outside.py')
            with self.assertRaises(ValueError):
                load_files(path)


if __name__ == '__main__':
    unittest.main()
