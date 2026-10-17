"""Minimal pairwise reranker training on the supplied data; no retrieval changes."""

import argparse
import json
from pathlib import Path
import random
import shutil

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

TOKENIZER_FILES = (
    "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
    "sentencepiece.bpe.model",
)


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


class TrainingPairs(Dataset):
    def __init__(self, records, corpus, seed=42):
        if not records:
            raise ValueError("training data is empty")
        self.records = records
        self.seed = seed
        self.positives = {}
        for row in records:
            if not isinstance(row.get("query"), str) or not row["query"].strip():
                raise ValueError("training query must be nonempty text")
            for field in ("pos", "neg"):
                value = row.get(field)
                if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                    raise ValueError(f"{field} must be an array of nonempty text strings")
            if not row["pos"]:
                raise ValueError("each query needs a positive")
            # Exclude all known positives for repeated copies of a query.
            self.positives.setdefault(row["query"], set()).update(x.strip() for x in row["pos"])
        self.pool = sorted({f"{doc.get('title', '')} {doc['text']}".strip() for doc in corpus})
        if not self.pool or "" in self.pool:
            raise ValueError("corpus must contain nonempty document text")

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        rng = random.Random(self.seed + index)
        known = self.positives[row["query"]]
        positive = rng.choice(row["pos"]).strip()
        negatives = [x.strip() for x in row["neg"] if x.strip() not in known]
        if negatives:
            negative = rng.choice(negatives)
        else:
            # The supplied neg arrays are empty. Sample a corpus document,
            # rejecting positives rather than training a single-candidate group.
            start = rng.randrange(len(self.pool))
            negative = next((self.pool[(start + offset) % len(self.pool)]
                             for offset in range(len(self.pool))
                             if self.pool[(start + offset) % len(self.pool)] not in known), None)
            if negative is None:
                raise ValueError("no negative outside known positives")
        return row["query"], positive, negative


def pairwise_loss(logits):
    if logits.ndim != 2 or logits.shape[1] != 1 or logits.shape[0] == 0 or logits.shape[0] % 2:
        raise ValueError("expected one logit per positive/negative pair")
    scores = logits.reshape(-1, 2)
    return torch.nn.functional.cross_entropy(
        scores, torch.zeros(scores.shape[0], dtype=torch.long, device=scores.device))


def save_checkpoint(model, source, destination):
    # save_pretrained may reserialize config/tokenizer metadata. Keep the exact
    # fixed originals required by the verifier, and save only weights anew.
    model.save_pretrained(destination, safe_serialization=True)
    for name in ("config.json", *TOKENIZER_FILES):
        shutil.copyfile(source / name, destination / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("/task/models/bge-reranker-base"))
    parser.add_argument("--train-data", type=Path, default=Path("/task/data/train.jsonl"))
    parser.add_argument("--corpus", type=Path, default=Path("/task/data/corpus.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("/app/output"), help="checkpoint goes in OUTPUT_DIR/model")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--max-steps", type=int, help="optional smoke-test limit")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if (min(args.batch_size, args.epochs, args.max_length) <= 0
            or not 0 < args.learning_rate < 1
            or (args.max_steps is not None and args.max_steps <= 0)):
        parser.error("batch size, epochs, lengths and step limit must be positive; learning rate must be in (0, 1)")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA unavailable; --device cpu is supported for a small smoke test")
    destination = args.output_dir / "model"
    if destination.exists() and any(destination.iterdir()):
        parser.error("output checkpoint directory is nonempty; choose a fresh --output-dir")
    for name in ("config.json", *TOKENIZER_FILES):
        if not (args.model / name).is_file():
            parser.error(f"missing backbone file: {name}")
    torch.manual_seed(args.seed)
    data = TrainingPairs(read_jsonl(args.train_data), read_jsonl(args.corpus), args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=False, use_safetensors=True)
    model.to(args.device).train()
    model.gradient_checkpointing_enable()

    def collate(rows):
        queries = [q for q, _, _ in rows for _ in range(2)]
        documents = [doc for _, positive, negative in rows for doc in (positive, negative)]
        return tokenizer(queries, documents, padding=True, truncation=True,
                         max_length=args.max_length, return_tensors="pt")

    loader = DataLoader(data, batch_size=args.batch_size, shuffle=True, collate_fn=collate,
                        generator=torch.Generator().manual_seed(args.seed))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
    steps = 0
    for _ in range(args.epochs):
        for encoded in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = pairwise_loss(model(**{k: v.to(args.device) for k, v in encoded.items()}).logits)
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            steps += 1
            if steps == 1 or steps % 50 == 0:
                print(json.dumps({"step": steps, "loss": loss.item(), "grad_norm": norm.item()}), flush=True)
            if args.max_steps is not None and steps >= args.max_steps:
                break
        if args.max_steps is not None and steps >= args.max_steps:
            break
    save_checkpoint(model, args.model, destination)
    print(json.dumps({"steps": steps, "checkpoint": str(destination)}), flush=True)


if __name__ == "__main__":
    main()
