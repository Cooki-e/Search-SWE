"""Submitted tokenizer sidecars must not change inference with fixed weights."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import torch
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          XLMRobertaConfig, XLMRobertaTokenizer)

import grader


class TokenizerIsolationTests(unittest.TestCase):
    def test_added_tokens_cannot_change_fixed_checkpoint_scores(self):
        # A small real XLM-R tokenizer/model keeps this regression offline and
        # independent of the downloaded 1 GB backbone. The legacy tokenizer
        # config matches the pinned backbone's added-token loading behavior.
        vocab = [(token, 0.0) for token in (
            "<s>", "<pad>", "</s>", "<unk>", "<mask>",
            "▁function", "function", "▁value", "value", "▁",
            "f", "u", "n", "c", "t", "i", "o",
        )]
        with tempfile.TemporaryDirectory() as directory:
            backbone = Path(directory) / "backbone"
            submitted = Path(directory) / "submitted"
            tokenizer = XLMRobertaTokenizer(vocab=vocab)
            tokenizer.save_pretrained(backbone)
            config_path = backbone / "tokenizer_config.json"
            config = json.loads(config_path.read_text())
            config.pop("added_tokens_decoder", None)
            config_path.write_text(json.dumps(config))
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(7)
                model = AutoModelForSequenceClassification.from_config(
                    XLMRobertaConfig(vocab_size=len(vocab), hidden_size=8,
                                     intermediate_size=16, num_attention_heads=2,
                                     num_hidden_layers=1, num_labels=1))
            model.save_pretrained(backbone)
            shutil.copytree(backbone, submitted)
            (submitted / "added_tokens.json").write_text(json.dumps({"function": 6}))
            for source in backbone.iterdir():
                self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),
                                 hashlib.sha256((submitted / source.name).read_bytes()).digest())

            # Establish that the attack changes real token IDs and logits,
            # without changing weights, architecture, or vocabulary size.
            trusted = AutoTokenizer.from_pretrained(backbone, local_files_only=True)
            unsafe = AutoTokenizer.from_pretrained(submitted, local_files_only=True)
            self.assertNotEqual(trusted("function value")["input_ids"],
                                unsafe("function value")["input_ids"])
            self.assertEqual(len(trusted), len(unsafe))
            pairs = [("function", "value")]
            device = torch.device("cpu")
            expected = grader.score_pairs(model, trusted, pairs, device)
            self.assertNotEqual(expected, grader.score_pairs(model, unsafe, pairs, device))

            # Exercise the same loader used for both formal scoring passes.
            with patch.object(grader, "BACKBONE_PATH", backbone):
                for checkpoint in (backbone, submitted):
                    with self.subTest(checkpoint=checkpoint.name):
                        actual_tokenizer, actual_model = grader.load_checkpoint(checkpoint)
                        grader.require_matching_architecture(model, actual_model)
                        self.assertEqual(trusted("function value")["input_ids"],
                                         actual_tokenizer("function value")["input_ids"])
                        self.assertEqual(expected, grader.score_pairs(
                            actual_model, actual_tokenizer, pairs, device))

    def test_malformed_submitted_sidecar_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)
            (checkpoint / "added_tokens.json").write_text("not JSON")
            with patch.object(grader.AutoTokenizer, "from_pretrained") as tokenizer, \
                    patch.object(grader.AutoModelForSequenceClassification, "from_pretrained"):
                grader.load_checkpoint(checkpoint)
            tokenizer.assert_called_once_with(grader.BACKBONE_PATH,
                                              local_files_only=True, trust_remote_code=False)


if __name__ == "__main__":
    unittest.main()
