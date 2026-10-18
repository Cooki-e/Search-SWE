# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

PDFs and questions are the MMLongBench-Doc and FinRAGBench-V branches of
[DocLensDatasets](https://huggingface.co/datasets/dwzhu/DocLensDatasets/tree/7a54da77adf09d2c88c67f1bbb725718260f1dc1).
The source evaluation code is
[DocLens](https://github.com/dwzhu-pku/DocLens/tree/1d7e6e6452c71b665b9029e5fef374357d9f3788).

Original PDFs are retained. Identical PDFs are shared across branches, yielding
433 documents and 29,149 pages. Uniformly extracted per-page text supplements
the PDFs. Questions identify the source document.

Four incorrect upstream answer-format fields are corrected deterministically;
questions, canonical answers and comparison rules remain unchanged.
Out-of-range source page references are excluded only from citation diagnostics.
Answer quality follows each source comparator, with the two branches equally
weighted. Citation diagnostics do not change the primary answer score.

The current package has 5 public input rows and 2,471 held-out rows.

## Source terms

The [fixed DocLens collection](https://huggingface.co/datasets/dwzhu/DocLensDatasets/tree/7a54da77adf09d2c88c67f1bbb725718260f1dc1) has no single dataset redistribution license established by the inspected fixed-release metadata. Preserve attribution to DocLens, MMLongBench-Doc, FinRAGBench-V and the original PDF publishers. The derived page text retains the source-document terms; extraction and answer-format corrections do not create new rights over those documents. Source-specific redistribution coverage remains a maintainer review item. Original PDFs stay at their verified upstream pins.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| dwzhu/DocLensDatasets | dataset | 7a54da77adf09d2c88c67f1bbb725718260f1dc1 | 433 |
| search-swe/Search-SWE | dataset | 299bcc817c8e795d8be1d20ad1dd39406be1263e | 436 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
