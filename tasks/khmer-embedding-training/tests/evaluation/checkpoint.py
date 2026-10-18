"""Validate checkpoint compatibility without importing submitted Python code."""
import hashlib
import json
from pathlib import Path
from safetensors import safe_open

TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "sentencepiece.bpe.model")
IGNORED_CONFIG = {"_name_or_path", "transformers_version", "torch_dtype", "dtype", "architectures"}

def file_hash(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
 return h.hexdigest()

def validate_checkpoint(checkpoint, backbone):
 checkpoint,backbone=Path(checkpoint),Path(backbone)
 if not checkpoint.is_dir():raise ValueError("Checkpoint must be a directory")
 expected=json.loads((backbone/"config.json").read_text())
 actual=json.loads((checkpoint/"config.json").read_text())
 if actual.get("auto_map") or actual.get("model_type")!="xlm-roberta":raise ValueError("Remote/custom architectures are not supported")
 from transformers import XLMRobertaConfig
 actual=XLMRobertaConfig.from_dict(actual).to_dict()
 expected=XLMRobertaConfig.from_dict(expected).to_dict()
 for cfg in (actual,expected):
  for k in IGNORED_CONFIG:cfg.pop(k,None)
 if actual!=expected:raise ValueError("The XLM-R architecture/configuration must remain unchanged")
 for name in TOKENIZER_FILES:
  if file_hash(checkpoint/name)!=file_hash(backbone/name):raise ValueError("Keep the supplied tokenizer unchanged: "+name)
 def shapes(root):
  result={}
  files=sorted(root.glob("*.safetensors"))
  if not files:raise ValueError("No safetensors weights")
  for p in files:
   with safe_open(p,framework="pt",device="cpu") as f:
    for key in f.keys():
     if key in {"embeddings.position_ids","embeddings.token_type_ids"}:continue
     if key in result:raise ValueError("Duplicate weight: "+key)
     result[key]=f.get_slice(key).get_shape()
  return result
 if shapes(checkpoint)!=shapes(backbone):raise ValueError("Parameter names/shapes do not match multilingual-e5-large")
 return {"architecture":"xlm-roberta","parameter_count":sum(__import__("math").prod(s) for s in shapes(backbone).values())}
