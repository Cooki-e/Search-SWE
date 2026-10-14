# Available Resources

Network access is disabled. This task needs no retrieval service or API key.

`/task/data/corpus.jsonl.gz` is the pinned Tevatron mirror of MS MARCO Passage
v1: 8,841,823 gzip JSONL records with `docid`, `text`, and extra `title`
metadata. Index only `text`. IDs cover 0 through 8841822 exactly.
SHA-256: `634543cee77a992613bbf32d0aa4863659dffd064c405f062454400aa80aea3f`.

`/task/data/warmup.jsonl.gz` contains 54 public DL20 queries with `query_id`
and `query`, without judgments. These are disjoint from dev and used for warmup.
SHA-256: `331e829922e2bd8ee1f01766fb7253c0d672ef79498011e91ad5e3e93f17a54a`.
Both files are read-only. Dev queries and qrels are verifier-only.

The starter pins byteorder 1.5.0, flate2 1.1.0, memmap2 0.9.5, rayon 1.10.0,
regex 1.11.1, rust-stemmers 1.2.0, serde 1.0.219, serde_json 1.0.140,
unicode-normalization 0.1.24 and zstd 0.13.3. Cargo.lock pins their transitive
dependencies. Generic crates in this cache are allowed; existing search/index
engines, prebuilt indexes and external data are not. All core indexing and
retrieval must be implemented in Rust.

Microsoft's MS MARCO dataset terms apply separately from the code license:
https://microsoft.github.io/msmarco/Datasets
