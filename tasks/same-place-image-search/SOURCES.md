# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

Gallery photographs and expert relevance judgments use
[Revisited Oxford/Paris](https://github.com/filipradenovic/revisitop/tree/be398328edcd17b3ad2ee6141949b700b85d2eb8),
with the source [Oxford](https://www.robots.ox.ac.uk/~vgg/data/oxbuildings/)
and [Paris](https://www.robots.ox.ac.uk/~vgg/data/parisbuildings/) image releases.

The prepared gallery has 11,315 photographs and 140 query crops. Exact decoded
duplicates of query-source images are removed. Original Hard positives remain
positive; original Easy and Junk items are per-query exclusions rather than
new negatives. No GPS-derived labels or webpage evidence are added.
The current top-five binary nDCG metric uses the source Hard protocol and
equally weights Oxford and Paris.

The current package has 5 public input rows and 135 held-out rows.

## Source terms

The original [Oxford](https://www.robots.ox.ac.uk/~vgg/data/oxbuildings/) and [Paris](https://www.robots.ox.ac.uk/~vgg/data/parisbuildings/) release pages require compliance with Flickr's Terms and Conditions and the Oxford Terms of Access. Both now state that image-download links are no longer available from those pages. The Revisited release supplies revised relevance judgments; it does not replace the original photograph terms. Retain Oxford/Paris and Revisited attribution, and review redistribution coverage for the mirrored images. Query cropping and duplicate removal are disclosed above. CLIP's [original notice](https://github.com/openai/CLIP/blob/main/LICENSE) is MIT.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| openai/clip-vit-base-patch32 | model | 3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268 | 8 |
| search-swe/Search-SWE | dataset | 1cc6fecdcf04f65bfe47fe6e2b7639a7b5766d47 | 11,323 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
