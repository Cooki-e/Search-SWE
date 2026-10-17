from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
import yaml


spec = importlib.util.spec_from_file_location("first_stage", Path(__file__).with_name("first_stage.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Tokenizer:
    def __init__(self):
        self.calls = []

    def __call__(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return {"input_ids": torch.tensor([[int(text), 0] for text in texts])}


class Encoder:
    device = torch.device("cpu")

    def __init__(self, vectors):
        self.vectors = torch.tensor(vectors, dtype=torch.float32)

    def __call__(self, input_ids):
        assert not torch.is_grad_enabled()
        cls = self.vectors[input_ids[:, 0]]
        # Non-CLS tokens deliberately differ so mean pooling fails the test.
        hidden = torch.stack((cls, torch.full_like(cls, 100)), dim=1)
        return SimpleNamespace(last_hidden_state=hidden)


class FrozenRetrieverTests(unittest.TestCase):
    def test_default_embedding_pool_contains_exactly_200_candidates(self):
        ids = [f"d{i:03d}" for i in range(201)]
        rows = list(module.candidates(ids, np.ones((201, 1)), [{"_id": "q"}], np.ones((1, 1))))
        self.assertEqual(rows[0]["docids"], ids[:200])

    def test_cls_pooling_normalization_and_candidate_order(self):
        vectors = module.embed(["0", "1"], Tokenizer(), Encoder([[3, 0], [0, 2]]))
        self.assertEqual(vectors.dtype, np.float32)
        self.assertTrue(np.allclose(vectors, [[1, 0], [0, 1]]))
        rows = list(module.candidates(["b", "a"], vectors,
                                      [{"_id": "q"}], np.array([[1.0, 0.0]]), k=2))
        self.assertEqual(rows, [{"qid": "q", "docids": ["b", "a"]}])
        tie = list(module.candidates(["b", "a"], vectors,
                                     [{"_id": "q"}], np.array([[1.0, 1.0]]), k=2))
        self.assertEqual(tie[0]["docids"], ["a", "b"])

    def test_batches_preserve_text_order_and_fixed_tokenization(self):
        texts = [str(i) for i in range(33)]
        expected = np.array([[i + 1, 1] for i in range(33)], dtype=np.float32)
        tokenizer = Tokenizer()
        vectors = module.embed(texts, tokenizer, Encoder(expected))
        self.assertTrue(np.allclose(vectors, expected / np.linalg.norm(expected, axis=1, keepdims=True)))
        self.assertEqual([call[0] for call in tokenizer.calls], [texts[:32], texts[32:]])
        for _, options in tokenizer.calls:
            self.assertEqual(options, dict(padding=True, truncation=True, max_length=512, return_tensors="pt"))

    def test_nonfinite_vectors_rejected(self):
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "invalid local embedding"):
                module.embed(["0"], Tokenizer(), Encoder([[value, 1]]))

    def test_zero_vector_rejected(self):
        with self.assertRaisesRegex(ValueError, "zero-length"):
            module.embed(["0"], Tokenizer(), Encoder([[0, 0]]))

    def test_bm25_matches_naive_formula_and_tokenization(self):
        self.assertEqual(module.tokenize("Foo_bar V2, BAZ!"), ["foo", "bar", "v2", "baz"])
        corpus = [{"_id": "b", "title": "APPLE", "text": "pear pear"},
                  {"_id": "c", "text": "apple banana " * 5},
                  {"_id": "a", "text": "banana pear"}, {"_id": "d", "text": "!!!"}]
        tokens = [Counter(module.tokenize((d.get("title", "") + " " + d["text"]).strip()))
                  for d in corpus]
        average = sum(sum(t.values()) for t in tokens) / len(tokens)
        for query in ("apple", "pear banana", "apple apple pear", "missing", "!!!"):
            scores = []
            for counts in tokens:
                score = 0.0
                for term in sorted(set(module.tokenize(query))):
                    df = sum(term in t for t in tokens)
                    idf = math.log(1 + (len(tokens) - df + 0.5) / (df + 0.5))
                    tf = counts[term]
                    score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * sum(counts.values()) / average))
                scores.append(score)
            expected = [corpus[i]["_id"] for i in sorted(range(4), key=lambda i: (-scores[i], corpus[i]["_id"]))]
            actual = list(module.bm25_candidates(corpus, [{"_id": "q", "text": query}], k=4))
            self.assertEqual(actual[0]["docids"], expected)
        self.assertEqual(list(module.bm25_candidates(corpus, [{"_id": "q", "text": "apple"}], k=4)),
                         list(module.bm25_candidates(corpus, [{"_id": "q", "text": "apple apple"}], k=4)))

    def test_bm25_zero_scores_and_too_small_corpus(self):
        corpus = [{"_id": "b", "text": "!!!"}, {"_id": "a", "text": "..."}]
        queries = [{"_id": "q", "text": "unseen"}]
        self.assertEqual(list(module.bm25_candidates(corpus, queries, k=2))[0]["docids"], ["a", "b"])
        with self.assertRaisesRegex(ValueError, "too few distinct"):
            list(module.bm25_candidates(corpus, queries))

    def test_rrf_overlap_one_based_ranks_and_ties(self):
        self.assertEqual(module.RRF_K, 60)
        self.assertEqual(module.rrf_fuse(["a", "shared"], ["b", "shared"]), ["shared", "a", "b"])
        self.assertEqual(module.rrf_fuse(["b", "a"], ["a", "b"]), ["a", "b"])
        self.assertEqual(module.rrf_fuse(["b", "a"], ["b", "a"]), ["b", "a"])
        # With k=60, ranks (1, 3) beat (2, 2); this also checks the reciprocal formula.
        self.assertEqual(module.rrf_fuse(["a", "b", "x"], ["y", "b", "a"])[0], "a")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.rrf_fuse(["a", "a"], ["b"])

    def test_rrf_matches_independent_reciprocal_sum(self):
        ids = [f"d{i:03d}" for i in range(320)]
        left = ids[:200]
        right = np.random.default_rng(17).permutation(ids[80:]).tolist()[:200]
        scores = {doc_id: sum(1.0 / (60 + branch.index(doc_id) + 1)
                             for branch in (left, right) if doc_id in branch)
                  for doc_id in set(left) | set(right)}
        self.assertEqual(module.rrf_fuse(left, right), sorted(scores, key=lambda d: (-scores[d], d)))

    def test_missing_local_model_does_not_fall_back_to_bm25(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(module, "MODEL_DIR", Path(directory) / "missing"), \
                    self.assertRaisesRegex(FileNotFoundError, "missing embedding checkpoint"):
                module.main()

    def test_metadata_matches_fixed_retrieval_contract(self):
        task = Path(__file__).resolve().parents[1]
        meta = tomllib.loads((task / "task.toml").read_text())["metadata"]
        self.assertEqual(meta["branch_candidate_count"], module.BRANCH_K)
        self.assertEqual(meta["candidate_pool_min_size"], module.BRANCH_K)
        self.assertEqual(meta["candidate_pool_max_size"], 2 * module.BRANCH_K)
        self.assertEqual(meta["rrf_k"], module.RRF_K)
        self.assertEqual(meta["bm25_k1"], module.BM25_K1)
        self.assertEqual(meta["bm25_b"], module.BM25_B)
        self.assertEqual(meta["embedding_batch_size"], module.EMBED_BATCH_SIZE)
        self.assertEqual(meta["embedding_max_length"], module.EMBED_MAX_LENGTH)

    def test_offline_phases_mount_both_models_and_no_public_validation(self):
        task = Path(__file__).resolve().parents[1]
        config = tomllib.loads((task / "task.toml").read_text())
        for phase in ("agent", "environment", "verifier"):
            self.assertEqual(config[phase]["network_mode"], "no-network")
            self.assertFalse(config[phase].get("allowed_hosts"))
            self.assertFalse(config[phase].get("env"))
        for phase in ("environment", "tests"):
            compose = yaml.safe_load((task / phase / "docker-compose.yaml").read_text())
            mounts = compose["services"]["main"]["volumes"]
            for model in ("bge-base-en-v1.5", "bge-reranker-base"):
                mount = next(m for m in mounts if m["target"] == f"/task/models/{model}")
                self.assertEqual(mount["source"], f"../models/{model}")
                self.assertTrue(mount["read_only"])
                self.assertFalse(mount["bind"]["create_host_path"])
            if phase == "environment":
                data_mounts = {m["target"] for m in mounts if m["target"].startswith("/task/data")}
                self.assertEqual(data_mounts, {"/task/data/corpus.jsonl", "/task/data/train.jsonl"})
                for mount in mounts:
                    source = (task / phase / mount["source"]).resolve()
                    self.assertNotEqual(source, task)
                    self.assertFalse(source.is_relative_to(task / "tests"))
        public_data = {e["path"] for e in json.loads((task / "assets.json").read_text())["files"]
                       if e["path"].startswith("data/")}
        self.assertEqual(public_data, {"data/corpus.jsonl", "data/train.jsonl"})

    def test_main_combines_two_200_branches_and_retains_private_union(self):
        corpus = [{"_id": f"d{i:03d}", "text": "A" * 600 + (" needle" if i >= 200 else "")}
                  for i in range(400)]
        queries = [{"_id": "q", "text": "needle" + " x" * 300}]
        vectors = np.array([[1., 0.]] * 200 + [[0., 1.]] * 200)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "corpus").write_text("".join(json.dumps(d) + "\n" for d in corpus))
            (root / "queries").write_text(json.dumps(queries[0]) + "\n")
            with patch.multiple(module, CORPUS=root / "corpus", QUERIES=root / "queries", OUTPUT=root / "private/results"), \
                    patch.object(module, "load_encoder", return_value=(object(), object())), \
                    patch.object(module, "embed", side_effect=[vectors, np.array([[1., 0.]])]) as embed:
                module.main()
            self.assertEqual(embed.call_args_list[0].args[0], ["A" * 512] * 400)
            self.assertEqual(embed.call_args_list[1].args[0], [queries[0]["text"][:512]])
            output = root / "private/results"
            row = json.loads(output.read_text())
            self.assertEqual(row["embedding_docids"], [d["_id"] for d in corpus[:200]])
            self.assertEqual(row["bm25_docids"], [d["_id"] for d in corpus[200:]])
            self.assertEqual(row["docids"], module.rrf_fuse(row["embedding_docids"], row["bm25_docids"]))
            self.assertEqual(len(set(row["docids"])), 400)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
