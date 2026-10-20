"""Validate the fixed checkpoint contract without importing submitted Python."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import stat

from safetensors import SafetensorError, safe_open

TOKENIZER_FILES = (
    "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
    "sentencepiece.bpe.model",
)
IGNORED_CONFIG = {
    "_name_or_path", "transformers_version", "torch_dtype", "dtype", "architectures",
}
IGNORED_WEIGHTS = {"embeddings.position_ids", "embeddings.token_type_ids"}


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_regular_file(path):
    path = Path(path)
    try:
        regular = stat.S_ISREG(path.lstat().st_mode)
    except FileNotFoundError:
        regular = False
    if not regular:
        raise ValueError("Missing or non-regular checkpoint file: " + path.name)


def parameter_shapes(path):
    require_regular_file(path)
    try:
        with safe_open(path, framework="pt", device="cpu") as weights:
            return {
                key: weights.get_slice(key).get_shape()
                for key in weights.keys() if key not in IGNORED_WEIGHTS
            }
    except SafetensorError as exc:
        raise ValueError("Invalid safetensors weights: " + str(exc)) from exc


def validate_checkpoint(checkpoint, backbone):
    checkpoint, backbone = Path(checkpoint), Path(backbone)
    if checkpoint.is_symlink() or not checkpoint.is_dir():
        raise ValueError("Checkpoint must be a self-contained directory")
    for name in ("config.json", "model.safetensors", *TOKENIZER_FILES):
        require_regular_file(checkpoint / name)
    expected = json.loads((backbone / "config.json").read_text())
    actual = json.loads((checkpoint / "config.json").read_text())
    if not isinstance(actual, dict):
        raise ValueError("config.json must contain a JSON object")
    if actual.get("auto_map") or actual.get("model_type") != "xlm-roberta":
        raise ValueError("Remote/custom architectures are not supported")
    from transformers import XLMRobertaConfig
    actual = XLMRobertaConfig.from_dict(actual).to_dict()
    expected = XLMRobertaConfig.from_dict(expected).to_dict()
    for config in (actual, expected):
        for key in IGNORED_CONFIG:
            config.pop(key, None)
    if actual != expected:
        raise ValueError("The XLM-R architecture/configuration must remain unchanged")
    for name in TOKENIZER_FILES:
        if file_hash(checkpoint / name) != file_hash(backbone / name):
            raise ValueError("Keep the supplied tokenizer unchanged: " + name)
    shapes = parameter_shapes(backbone / "model.safetensors")
    if parameter_shapes(checkpoint / "model.safetensors") != shapes:
        raise ValueError("Parameter names/shapes do not match multilingual-e5-large")
    return {
        "architecture": "xlm-roberta",
        "parameter_count": sum(math.prod(shape) for shape in shapes.values()),
    }


def load_standard_checkpoint(checkpoint):
    """Run by the grader in an offline, unprivileged child process."""
    from transformers import AutoModel, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False,
    )
    model, loading = AutoModel.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False,
        use_safetensors=True, output_loading_info=True,
    )
    for field in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"):
        values = loading.get(field, [])
        if field in ("missing_keys", "unexpected_keys"):
            values = [key for key in values if key not in IGNORED_WEIGHTS]
        if values:
            raise ValueError("Incomplete standard checkpoint load: " + field)
    return {
        "model_class": type(model).__name__,
        "tokenizer_class": type(tokenizer).__name__,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-standard", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(load_standard_checkpoint(args.load_standard), allow_nan=False))
