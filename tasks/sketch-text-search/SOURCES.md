# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

Artwork images, original sketches, descriptions and targets originate from
[CIRThan](https://github.com/jinyuxu-whut/CIRThan/tree/b1499eb9393b12f1499a983f8fedfe7d14869024).
The collection retains 2,287 artworks, 5,604 training queries and three
description levels.

This task explicitly changes the sketch input condition. Every sketch keeps a
deterministic left or right 60 percent in its original coordinate frame, masking
the other 40 percent. The side depends only on the opaque sketch ID, not target
labels or model results. Original descriptions and targets are unchanged.
Full sketches remain outside the task input.

Evaluation families are split together across all three description levels.
The current metric is level-macro 0.5 Recall@3 + 0.5 MRR@3, a task-specific
combination. It is not the original full-sketch paper setting.

The current package has 15 public input rows and 1,242 held-out rows.
Multiple versions of one original question stay in the same split; public
input-row counts therefore exceed the five public question families.

## Source terms

The [pinned CIRThan repository notice](https://github.com/jinyuxu-whut/CIRThan/blob/b1499eb9393b12f1499a983f8fedfe7d14869024/LICENSE) is MIT for the software and associated material. Original artworks and photographs retain their rightsholders' terms; that software notice alone does not establish a blanket image-redistribution grant. Image-rights coverage remains a maintainer review item. Preserve CIRThan attribution and disclose the deterministic sketch masking described above. CLIP's [original notice](https://github.com/openai/CLIP/blob/main/LICENSE) is MIT.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| openai/clip-vit-base-patch32 | model | 3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268 | 8 |
| search-swe/Search-SWE | dataset | 7762fe4b37bd2dcc6b2264cd0966c2065c6985ca | 4,165 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
