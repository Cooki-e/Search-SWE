# Available Resources

Both task phases run without network access or task API keys. Two read-only model directories are supplied: `/task/models/bge-reranker-base` is the starting checkpoint to fine-tune, and `/task/models/bge-base-en-v1.5` contains the frozen `BAAI/bge-base-en-v1.5` encoder for local inference. You may use the encoder to mine training candidates or evaluate a split held out from the supplied training data. Keep the encoder fixed. Use only the supplied models and data; external APIs, models, relevance datasets and retrieval/reranking services are prohibited. The verifier independently loads its own read-only copy of the encoder and builds the shared candidates locally.

## Fixed hybrid candidates

- **Embedding branch:** strip `title + " " + text`, take its first 512 characters;
  take the question's first 512 characters. Add no query instruction or prefix.
  Load `AutoTokenizer` and `AutoModel` from `/task/models/bge-base-en-v1.5`
  with `local_files_only=True` and `trust_remote_code=False`; require
  `use_safetensors=True` for the model. Use evaluation mode, float32, batch size
  32, padding and tokenizer truncation to 512 tokens. Take the final hidden
  state of the first (CLS) token, L2-normalize the float32 vectors, rank by
  cosine similarity and keep exactly 200 IDs.
- **Local BM25 branch:** index full stripped `title + " " + text` and use full
  questions. Tokens are lowercase ASCII `[a-z0-9]+` matches (underscores and
  punctuation split tokens); no stemming or stopwords. Each distinct query
  token contributes once, in sorted token order for deterministic summation.
  With `N` corpus documents, document frequency `df(t)`, token count `dl`, and
  mean token count `avgdl` over all corpus documents, score each document by:

  `sum_t log(1 + (N-df(t)+0.5)/(df(t)+0.5)) * tf(t,d)*2.2 / (tf(t,d) + 1.2*(0.25 + 0.75*dl/avgdl))`

  Only query tokens present in the document contribute. An all-empty-token
  corpus yields zero scores. Take exactly 200 IDs, even when that requires
  zero-score documents. BM25 mining uses the supplied corpus without model inference.
- **Fusion:** for each document in either list, sum `1/(60 + rank)` over the
  lists containing it; rank is 1-based and both weights are 1. Keep the full
  deduplicated union, without further truncation or padding (200–400 IDs).
  Sort by descending fused score. All branch/fusion ties use ascending ID.

The verifier validates both private branch lists and the full RRF ordering, then
scores identical candidates with baseline and submitted rerankers. First-stage
scores are not blended with neural scores; only exact neural-score ties retain
RRF order. You may use this policy to mine supplied training data, but the
verifier's retrieval configuration is fixed and cannot be optimized by the agent.
