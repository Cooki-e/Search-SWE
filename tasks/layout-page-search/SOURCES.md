# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

Current inputs derive from the MMLongBench-Doc branch of
[DocLensDatasets](https://huggingface.co/datasets/dwzhu/DocLensDatasets/tree/7a54da77adf09d2c88c67f1bbb725718260f1dc1).

Selection retains original questions whose evidence includes Chart, Figure or
Generalized-text/Layout, whose evidence pages exist, and whose complete evidence
set fits ten pages. This gives 520 questions over 119 documents and 5,294 rendered
pages. Original question wording and evidence-page sets are retained.

The request specifies its document. The task-specific metric is evidence-page
set F1, not the earlier ViDoRe V2 four-collection nDCG prototype. This dataset
overlaps the source used by visual-document-qa, but returns page sets rather
than answers. No independent layout-hardness annotation is claimed.

The current package has 5 public input rows and 515 held-out rows.

## Source terms

The original [MMLongBench-Doc license section](https://github.com/mayubo2333/MMLongBench-Doc#-license)
specifies CC BY-NC 4.0 for data and Apache-2.0 for code. Preserve the data-specific
attribution and noncommercial terms for the selected questions, annotations and
derived pages; the code license does not replace those data terms.

Retain attribution to DocLens, MMLongBench-Doc and the individual PDF publishers.
The dataset-level statement does not independently establish rights over every
third-party PDF or its rendered pages; that source-specific coverage remains a
maintainer review item. Rendering and evidence-category selection are disclosed
adaptations. The supplied ColQwen2.5 adapter is MIT and its compatible base is
Apache-2.0.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| search-swe/Search-SWE | dataset | 8bd2c2c661e9ebf33925a5b110630af6dd923fbc | 5,297 |
| vidore/colqwen2.5-base | model | 92908120384b7a2110c5beda3ab29cbdb2c08e49 | 14 |
| vidore/colqwen2.5-v0.2 | model | dcbe8d9cede518bce830488364ba0e40c873645b | 13 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
