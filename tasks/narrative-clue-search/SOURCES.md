# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

Inputs use the [TREC Tip-of-the-Tongue 2023 movie collection](https://trec-tot.github.io/guidelines-2023).
Original test judgments are obtained from the
[2024 dev2 release](https://trec-tot.github.io/guidelines-2024), which republishes
the 2023 test set.

All 450 human recollections are retained. The source archive has 231,852 rows:
26 empty-text records and both entries under one ambiguous nonempty document ID
are removed, leaving 231,824 articles. Gold targets are verified unaffected.
Query inputs omit target links and answer metadata. Original human sentence
annotations are provided only for public questions.

The task uses mean nDCG@10 over held-out questions. Four narrative/uncertainty
groups are diagnostics and do not reweight the primary metric.

The current package has 5 public input rows and 445 held-out rows.

## Source terms

The question bodies originate from Microsoft's
[MS-TOT collection](https://github.com/microsoft/Tip-of-the-Tongue-Known-Item-Retrieval-Dataset-for-Movie-Identification),
whose [content license](https://github.com/microsoft/Tip-of-the-Tongue-Known-Item-Retrieval-Dataset-for-Movie-Identification/blob/main/LICENSE)
is CC BY-SA 4.0. Preserve attribution and the share-alike terms for adapted
question text. All 450 retained question bodies match that source after
normalizing whitespace and HTML entities and removing the task's title line.

Retain attribution to the [TREC 2023 collection](https://trec-tot.github.io/guidelines-2023)
and its [2024 dev2 release](https://trec-tot.github.io/guidelines-2024).
The question-body match does not establish a separate license for every TREC
annotation field. Wikipedia article text retains its applicable attribution and
share-alike terms. Removal of malformed corpus records and answer-metadata
stripping are task adaptations; no blanket replacement license is asserted.

## Runtime asset sources

All remote manifest entries use immutable revisions.

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| search-swe/Search-SWE | dataset | 36a2da8a33879eed413f5be3a41fdad04b1ea157 | 4 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
