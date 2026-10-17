# Fixed input provenance

Updated against Search-SWE `f1c4f57` and `tasks/long-pdf-evidence` v0.4.1 on 2026-10-16. `assets.json` is the exact byte-level public input contract. The PDF is unchanged; the sentence inventory and revised public examples replace the previous page-based task data.

| Local input | Official source path | Immutable revision |
| --- | --- | --- |
| `data/corpus/lp4P6AUxur.pdf` | `tasks/long-pdf-evidence/corpus/lp4P6AUxur.pdf` | `6713b1eb7474e0768e906a0151c76af92f0cfcdd` |
| `data/corpus/sentences.jsonl` | `tasks/long-pdf-evidence/corpus/sentences.jsonl` | `2a2188f3a9426361da5f10c82a35148269574a92` |
| `data/validation/queries.jsonl` | `tasks/long-pdf-evidence/validation/queries.jsonl` | `872d710516ecfbc39f1557ebd750733e727dfc49` |
| `data/validation/golden_answers.jsonl` | `tasks/long-pdf-evidence/validation/golden_answers.jsonl` | `872d710516ecfbc39f1557ebd750733e727dfc49` |

All sources are in [search-swe/Search-SWE](https://huggingface.co/datasets/search-swe/Search-SWE/tree/872d710516ecfbc39f1557ebd750733e727dfc49). The latest public examples use canonical `validation/` paths; old page-based examples are not part of this revision. Private questions and references are copied byte-for-byte from the reviewed Git package at `f1c4f57`, under `tests/data/`, excluded from agent mounts.

## Origin and terms

The [dataset source record](https://huggingface.co/datasets/search-swe/Search-SWE/blob/872d710516ecfbc39f1557ebd750733e727dfc49/SOURCES.md) identifies Leo Tolstoy's *War and Peace*, translated by Louise and Aylmer Maude in 1922–23, in a 2016 PDF edition edited by Daniel Studzinski. The underlying Maude translation is identified as public domain in the USA by [Project Gutenberg](https://www.gutenberg.org/ebooks/2600). That does not grant a blanket license over the PDF edition's artwork, fonts or design.

Bingyu's question-independent inventory contains 28,798 fixed units with normalized typography/whitespace and physical-page provenance, including dialogue and cross-page sentences. The ten public and twelve hidden questions have independent opaque IDs and disjoint reference sentence units. Sufficient references are not an exhaustive list of acceptable evidence. Preserve attribution and applicable terms; pin/hash agreement alone does not establish redistribution rights. No upload was performed.

## Publication readiness

These four inputs retain the original task's verified published paths and immutable pins. No duplicate upload is needed. Search-SWE `ac7dcc1` accepts published official inputs from another task's namespace; new uploads still require their publishing task's namespace. On 2026-10-17, both checkouts and remote main contained this fix. The unchanged manifest passed the contribution checkout's merge-ready checker and all four local asset hash checks.

The hidden files are private to the verifier at runtime, but public repository readers can see them. Asset verification, grader checks and configured-model evaluation are separate evidence layers; see the task README and authoring records for their status.

An earlier offline duplicate-publication proposal under
`contributing/dev/long-pdf-evidence-vectorless/2026-10-17/` was cancelled after
the contributor requested direct reuse. No upload or HF PR occurred. Public
wording remains unchanged at the contributor's request, and `assets.json`
still contains the same evaluated sources, sizes and hashes.
