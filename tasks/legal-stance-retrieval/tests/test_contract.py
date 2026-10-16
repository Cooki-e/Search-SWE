"""Author-side tests; these do not call APIs or use a GPU."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import grader
import finalize_reward


class OutputAndMetric(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'results.jsonl'
        self.queries = [{'query_id': 'a', 'query': 'Claim', 'stance': 'all'}]
        self.ids = {f'd{i}' for i in range(12)}
        self.order = {f'd{i}': i for i in range(12)}
        self.row = {'query_id': 'a', 'results': [
            {'doc_id': f'd{i}', 'score': 10-i} for i in range(10)]}

    def validate(self, rows):
        self.path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        return grader.validate_output(self.queries, self.ids, self.order, output_path=self.path)

    def test_valid_top10_and_known_ndcg(self):
        row = self.validate([self.row])[0]
        report = grader.score_results([row], {'a': {'d1', 'd3', 'd11'}})
        expected = (1/math.log2(3) + 1/math.log2(5)) / sum(1/math.log2(i+2) for i in range(3))
        self.assertAlmostEqual(report['mean_ndcg_at_10'], expected)

    def test_perfect_ranking_more_than_ten_gold(self):
        self.assertEqual(grader.ndcg_at_10([f'd{i}' for i in range(10)], self.ids), 1)

    def test_aggregate_then_normalize(self):
        rows = [{'query_id': 'a', 'results': ['yes']}, {'query_id': 'b', 'results': ['no']}]
        result = grader.score_results(rows, {'a': {'yes'}, 'b': {'yes'}})
        self.assertEqual(result['mean_ndcg_at_10'], .5)
        self.assertEqual(result['reward'], 0)  # Per-query normalization would incorrectly give .5.
        self.assertEqual(grader.normalize_score(grader.BASELINE_B), 0)
        self.assertEqual(grader.normalize_score(1), 1)
        self.assertAlmostEqual(grader.normalize_score((1+grader.BASELINE_B)/2), .5)

    def test_bad_coverage(self):
        for rows in ([], [self.row, self.row], [dict(self.row, query_id='other')]):
            with self.subTest(rows=rows), self.assertRaises(grader.VerificationError):
                self.validate(rows)

    def test_invalid_results(self):
        mutations = [[], self.row['results'][:9], self.row['results'] + [self.row['results'][0]],
                     [dict(item, score=True) for item in self.row['results']],
                     [dict(item, score=float('nan')) for item in self.row['results']],
                     [dict(item, score=float('inf')) for item in self.row['results']],
                     [dict(item, score='1') for item in self.row['results']],
                     [dict(item, doc_id='absent') for item in self.row['results']],
                     [dict(item, doc_id=3) for item in self.row['results']],
                     [self.row['results'][0]]*10, self.row['results'][::-1]]
        for results in mutations:
            with self.subTest(results=results), self.assertRaises(grader.VerificationError):
                self.validate([dict(self.row, results=results)])

    def test_ties_follow_returned_order(self):
        result = self.validate([dict(self.row, results=[dict(r, score=0) for r in self.row['results'][::-1]])])
        self.assertEqual(result[0]['results'][0], 'd9')

    def test_missing_or_malformed_output(self):
        for text in (None, '{oops}\n', '[]\n'):
            if text is not None:
                self.path.write_text(text)
            with self.assertRaises(grader.VerificationError):
                grader.validate_output(self.queries, self.ids, self.order, output_path=self.path)

    def test_frozen_baseline_and_dataset_hashes(self):
        import hashlib
        private = Path(__file__).parent / 'data'
        anchor = json.loads((private / 'normalization.json').read_text())
        self.assertEqual(grader.BASELINE_B, anchor['baseline_B'])
        for name, field in [('queries.jsonl', 'test_queries_sha256'), ('ground_truth.jsonl', 'qrels_sha256')]:
            self.assertEqual(hashlib.sha256((private / name).read_bytes()).hexdigest(), anchor[field])
        with patch.object(grader, 'PRIVATE_DATA', private):
            gold_rows = grader.read_jsonl(private / 'ground_truth.jsonl')
            corpus_ids = set().union(*(row['relevance'] for row in gold_rows))
            queries, gold = grader.load_private_data(corpus_ids)
        self.assertEqual(len(queries), 311)
        self.assertEqual(sum(map(len, gold.values())), 732)
        self.assertEqual({q['stance'] for q in queries}, {'all', 'supported', 'refuted'})


class WholeSuiteDeadline(unittest.TestCase):
    def run_case(self, run_status, *, build_status=None, write_output=True):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            q = [{'query_id': str(i), 'query': 'claim', 'stance': 'all'} for i in range(3)]
            ids = {f'd{i}' for i in range(10)}
            order = {f'd{i}': i for i in range(10)}
            events = []
            def stage(queries):
                self.assertEqual(len(queries), 3)
                events.append('stage')
                return root / 'queries.jsonl'
            def run(command, **kwargs):
                if command[0].endswith('build.sh'):
                    events.append('build')
                    self.assertEqual(kwargs['timeout'], 3600)
                    return build_status or {'returncode': 0, 'timed_out': False, 'elapsed_seconds': .1}
                events.append('run')
                self.assertEqual(kwargs['timeout'], 20)
                if write_output:
                    (root/'results.jsonl').write_text(''.join(json.dumps({
                        'query_id': r['query_id'], 'results': [
                            {'doc_id': f'd{i}', 'score': 10-i} for i in range(10)]})+'\n' for r in q))
                return run_status
            with patch.multiple(grader, RESULTS_DIR=root, REPORT_PATH=root/'evaluation.json',
                                OUTPUT_PATH=root/'results.jsonl', EXECUTION_ERROR=''), \
                 patch.object(grader, 'recreate_workdirs'), \
                 patch.object(grader, 'load_corpus', return_value=(ids, order)), \
                 patch.object(grader, 'load_private_data', return_value=(q, {r['query_id']: {'d0'} for r in q})), \
                 patch.object(grader, 'check_submission_boundary'), \
                 patch.object(grader, 'stage_queries', side_effect=stage), \
                 patch.object(grader, 'run_timed', side_effect=run) as timed, \
                 patch.object(grader, 'stop_submission_processes') as stop:
                status = grader.main()
                self.assertTrue(stop.called)
                report = json.loads((root/'evaluation.json').read_text())
                return status, report, events, timed.call_count

    def test_single_call_after_build(self):
        status, report, events, calls = self.run_case({'returncode': 0, 'timed_out': False, 'elapsed_seconds': 1})
        self.assertEqual((status, calls), (0, 2))
        self.assertEqual(events, ['build', 'stage', 'run'])
        self.assertEqual(report['reward'], 1)

    def test_timeout_rejects_even_complete_correct_output(self):
        status, report, _, _ = self.run_case({'returncode': -9, 'timed_out': True, 'elapsed_seconds': 20.2})
        self.assertEqual(status, 1)
        self.assertFalse(report['valid'])
        self.assertEqual(report['reward'], 0)

    def test_late_success_and_nonzero_exit_fail(self):
        for code, elapsed in [(0, 20.001), (1, 1)]:
            status, report, _, _ = self.run_case({'returncode': code, 'timed_out': False, 'elapsed_seconds': elapsed})
            self.assertEqual(status, 1)
            self.assertEqual(report['reward'], 0)

    def test_build_failure_does_not_reveal_queries(self):
        status, report, events, _ = self.run_case({}, build_status={'returncode': 1, 'timed_out': False, 'elapsed_seconds': 1})
        self.assertEqual(events, ['build'])
        self.assertEqual(status, 1)
        self.assertEqual(report['reward'], 0)

    def test_missing_output_fails(self):
        status, report, _, _ = self.run_case({'returncode': 0, 'timed_out': False, 'elapsed_seconds': 1}, write_output=False)
        self.assertEqual(status, 1)
        self.assertEqual(report['reward'], 0)

    def test_real_process_group_timeout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(grader, 'SUBMISSION_DIR', root), patch.object(grader, 'submission_command', side_effect=lambda c:c):
                result = grader.run_timed(['/bin/sh', '-c', 'sleep 10 & wait'], timeout=.1,
                                          stdout_path=root/'out', stderr_path=root/'err')
            self.assertTrue(result['timed_out'])
            self.assertLess(result['elapsed_seconds'], 3)


class RewardGate(unittest.TestCase):
    def test_required_audit_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evaluation = root/'evaluation.json'
            reward = root/'reward.json'
            trajectory = root/'trajectory.json'
            trajectory.write_text('{}')
            with patch.multiple(finalize_reward, REWARD_DIR=root, EVALUATION_PATH=evaluation,
                                JUDGE_REWARD_PATH=reward, DETAILS_PATH=root/'details.json', TRAJECTORY_PATH=trajectory):
                for valid, status, judge, expected in [(True,'0',1,.5), (False,'0',1,0),
                                                       (True,'78',1,0), (True,'0',0,0), (True,'0',None,0)]:
                    evaluation.write_text(json.dumps({'valid':valid, 'mean_ndcg_at_10': .8, 'primary_metric':{'value':.5}}))
                    reward.write_text(json.dumps({'jailbreak_judge':judge}))
                    with patch.object(finalize_reward, 'JUDGE_STATUS', status):
                        finalize_reward.main()
                    self.assertEqual(json.loads(reward.read_text())['reward'], expected)
                    self.assertEqual(float((root/'reward.txt').read_text()), expected)
                trajectory.unlink()
                reward.write_text('{"jailbreak_judge":1}')
                with patch.object(finalize_reward, 'JUDGE_STATUS', '0'):
                    finalize_reward.main()
                self.assertEqual(float((root/'reward.txt').read_text()), 0)


if __name__ == '__main__':
    unittest.main()
