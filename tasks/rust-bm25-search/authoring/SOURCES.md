# Input and tool provenance

The fixed runtime inputs are listed with exact sizes, SHA-256 digests and
immutable HF commits in `../assets.json`. The corpus is the existing
`Tevatron/msmarco-passage-corpus` mirror, revision
`21a2e1a8c6e7b1747c92f82cd2259a97077dc48d`. The 54 DL20 query texts come from
`Tevatron/msmarco-passage`, revision
`330a160b40a739d4c07d52c7ce562e2c549214c0`. No new public upload was made.

The corpus gzip was hashed locally and all 8,841,823 unique canonical IDs were
checked during conversion. Only the `text` field is indexed; the mirror's
additional `title` field is deliberately excluded. The query split was checked
for overlap by query ID and normalized text.

Verifier-only dev topics and qrels originate in `castorini/anserini-tools`,
commit `8f1bc80988c2483d9519bc2519862b54ab730986`. Exact source URLs, source
hashes and the derived query-file hash are in `../tests/data/sources.json`.
`prepare_queries.py` restores them without accessing a mutable branch. The
small verifier inputs are included only in the verifier image; they are not
mounted in the agent environment.

MS MARCO is a Microsoft dataset. Its official
[dataset page and terms](https://microsoft.github.io/msmarco/Datasets#terms-and-conditions),
checked on 2026-10-11, restrict use to non-commercial research and say that
availability does not extend a license or other intellectual-property rights.
The page separately licenses repository documentation and code; those notices
do not establish a redistribution grant for the underlying passages. Tevatron
mirroring does not establish new redistribution rights either. Maintainers must
resolve the applicable MS MARCO/TREC terms and the proposed official mirror
before publication. No new dataset license or redistribution grant is asserted
here. The dataset page requests citation of the
[MS MARCO dataset paper](https://arxiv.org/abs/1611.09268).

Both images use `docker.io/hanhainebula/search-swe-base:cpu-py3.12-1.0.0`.
The locally inspected base digest is
`sha256:1350a3043b3c49388b48dd5a0c2e3d91e9071f87359dbe63a2c26f055acb0cd2`.
It supplies Pyserini 1.4.0 and Java 21. The Rust 1.85.1 distribution's source
URL and verified checksum are in the two matching `install-rust.sh` files.
Cargo.lock pins every dependency by version and registry checksum. The agent
and verifier use the same toolchain/cache seed.

`reference-observation.json` records the full local baseline run and its
input hashes. `../tests/reference-quality.json` pins its exact quality result,
not its host-specific timings. Each valid candidate verifier run rebuilds and
measures the reference again on the same container resource profile.
