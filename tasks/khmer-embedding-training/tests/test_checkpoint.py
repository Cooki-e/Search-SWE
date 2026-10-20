"""Checkpoint contract regressions using a small locally created model."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

MODULE_PATH = Path(__file__).parent / "evaluation" / "checkpoint.py"
spec = importlib.util.spec_from_file_location("checkpoint_contract", MODULE_PATH)
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


class CheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tokenizers import Tokenizer
        from tokenizers.models import WordLevel
        from tokenizers.pre_tokenizers import Whitespace
        from transformers import PreTrainedTokenizerFast, XLMRobertaConfig, XLMRobertaModel
        cls.temp = tempfile.TemporaryDirectory()
        cls.backbone = Path(cls.temp.name) / "backbone"
        config = XLMRobertaConfig(
            vocab_size=16, hidden_size=8, num_hidden_layers=1,
            num_attention_heads=2, intermediate_size=16,
            max_position_embeddings=32, type_vocab_size=1,
            pad_token_id=0, bos_token_id=1, eos_token_id=2,
        )
        XLMRobertaModel(config).save_pretrained(cls.backbone, safe_serialization=True)
        tokenizer = Tokenizer(WordLevel(
            {"[PAD]": 0, "[CLS]": 1, "[SEP]": 2, "[UNK]": 3, "hello": 4},
            unk_token="[UNK]",
        ))
        tokenizer.pre_tokenizer = Whitespace()
        PreTrainedTokenizerFast(
            tokenizer_object=tokenizer, unk_token="[UNK]", pad_token="[PAD]"
        ).save_pretrained(cls.backbone)
        (cls.backbone / "special_tokens_map.json").write_text(
            json.dumps({"unk_token": "[UNK]", "pad_token": "[PAD]"})
        )
        # This contract also requires an unchanged SentencePiece file.
        (cls.backbone / "sentencepiece.bpe.model").write_bytes(b"fixture-sentencepiece")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.model = Path(self.temp.name) / "model"
        shutil.copytree(self.backbone, self.model)

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_standard_checkpoint_passes(self):
        self.assertGreater(
            checkpoint.validate_checkpoint(self.model, self.backbone)["parameter_count"], 0
        )
        loaded = checkpoint.load_standard_checkpoint(self.model)
        self.assertEqual(loaded["model_class"], "XLMRobertaModel")

    def test_renamed_weights_are_rejected(self):
        (self.model / "model.safetensors").rename(self.model / "nonstandard.safetensors")
        with self.assertRaisesRegex(ValueError, "model.safetensors"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_weight_symlink_is_rejected(self):
        weights = self.model / "model.safetensors"
        weights.unlink()
        weights.symlink_to(self.backbone / "model.safetensors")
        with self.assertRaisesRegex(ValueError, "model.safetensors"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_malformed_weights_are_submission_errors(self):
        (self.model / "model.safetensors").write_bytes(b"not-safetensors")
        with self.assertRaises(ValueError):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_changed_tokenizer_is_rejected(self):
        (self.model / "tokenizer_config.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "tokenizer"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_missing_tokenizer_is_rejected(self):
        (self.model / "tokenizer.json").unlink()
        with self.assertRaisesRegex(ValueError, "tokenizer.json"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_non_object_config_is_rejected(self):
        (self.model / "config.json").write_text("[]")
        with self.assertRaisesRegex(ValueError, "JSON object"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_changed_architecture_is_rejected(self):
        path = self.model / "config.json"
        config = json.loads(path.read_text())
        config["hidden_size"] += 8
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "configuration"):
            checkpoint.validate_checkpoint(self.model, self.backbone)

    def test_standard_loader_rejects_renamed_weights(self):
        (self.model / "model.safetensors").rename(self.model / "nonstandard.safetensors")
        with self.assertRaises(OSError):
            checkpoint.load_standard_checkpoint(self.model)

    def test_standard_loader_cli_works_offline(self):
        result = subprocess.run(
            [sys.executable, "-I", str(MODULE_PATH), "--load-standard", str(self.model)],
            env={
                "PATH": "/usr/bin:/bin", "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["model_class"], "XLMRobertaModel")

    def test_baseline_records_the_current_validator(self):
        baseline = json.loads((Path(__file__).parent / "data/baseline.json").read_text())
        self.assertEqual(
            baseline["fingerprint"]["checkpoint_validator"],
            hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
