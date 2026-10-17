"""Training-signal, data-format and checkpoint compatibility regressions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import torch
from transformers import AutoModelForSequenceClassification, XLMRobertaConfig


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
starter = load_module("reranker_starter", ROOT / "environment/starter/train.py")
grader = load_module("reranker_grader", ROOT / "tests/grader.py")


class StarterTests(unittest.TestCase):
    def test_empty_negatives_are_filled_without_using_any_known_positive(self):
        rows = [{"query": "q", "pos": ["one"], "neg": []},
                {"query": "q", "pos": ["two"], "neg": []}]
        corpus = [{"text": text} for text in ("one", "two", "negative")]
        pairs = starter.TrainingPairs(rows, corpus)
        self.assertEqual(pairs[0], ("q", "one", "negative"))
        self.assertEqual(pairs[1], ("q", "two", "negative"))
        self.assertEqual(pairs[0], starter.TrainingPairs(rows, corpus)[0])

    def test_string_encoded_lists_rejected(self):
        with self.assertRaisesRegex(ValueError, "pos must be an array"):
            starter.TrainingPairs([{"query": "q", "pos": '["one"]', "neg": []}], [{"text": "one"}])

    def test_no_usable_negative_fails(self):
        pairs = starter.TrainingPairs([{"query": "q", "pos": ["one"], "neg": ["one"]}], [{"text": "one"}])
        with self.assertRaisesRegex(ValueError, "no negative"):
            pairs[0]

    def test_two_candidate_loss_updates_weights_and_reduces_loss(self):
        model = torch.nn.Linear(1, 1, bias=False)
        torch.nn.init.zeros_(model.weight)
        examples = torch.tensor([[1.0], [-1.0]])
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        before = starter.pairwise_loss(model(examples))
        before.backward()
        self.assertGreater(model.weight.grad.abs().sum().item(), 0)
        optimizer.step()
        after = starter.pairwise_loss(model(examples))
        self.assertLess(after.item(), before.item())

    def test_single_candidate_cannot_silently_train_with_zero_loss(self):
        # Demonstrate the legacy objective's degeneracy, then reject it here.
        scores = torch.tensor([[2.0], [4.0]], requires_grad=True)
        old_loss = torch.nn.functional.cross_entropy(scores, torch.zeros(2, dtype=torch.long))
        old_loss.backward()
        self.assertEqual(old_loss.item(), 0)
        self.assertEqual(scores.grad.abs().sum().item(), 0)
        with self.assertRaisesRegex(ValueError, "positive/negative"):
            starter.pairwise_loss(torch.tensor([[2.0]], requires_grad=True))

    def test_checkpoint_roundtrip_matches_grader_and_preserves_metadata_bytes(self):
        config = XLMRobertaConfig(vocab_size=32, hidden_size=8, intermediate_size=16,
                                  num_attention_heads=2, num_hidden_layers=1, num_labels=1)
        model = AutoModelForSequenceClassification.from_config(config)
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "original", Path(directory) / "trained"
            model.save_pretrained(source)
            for name in starter.TOKENIZER_FILES:
                # Metadata byte-copy fixture; actual tokenizer loading is covered
                # by the separate BGE CPU smoke test, not these placeholder bytes.
                (source / name).write_bytes(json.dumps({"fixture": name}).encode())
            original = AutoModelForSequenceClassification.from_pretrained(source, local_files_only=True, use_safetensors=True)
            starter.save_checkpoint(model, source, output)
            trained = AutoModelForSequenceClassification.from_pretrained(output, local_files_only=True, use_safetensors=True)
            grader.require_matching_architecture(original, trained)
            self.assertTrue((output / "model.safetensors").is_file())
            for name in ("config.json", *starter.TOKENIZER_FILES):
                self.assertEqual((source / name).read_bytes(), (output / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
