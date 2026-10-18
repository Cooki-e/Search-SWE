# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

Original Charades-STA and ActivityNet Captions descriptions and intervals use
the [Lighthouse release](https://github.com/line/lighthouse/tree/3e841d3d662c8440afed514908566fed2d5e82a7)
and its released CLIP ViT-B/32 video features.

The sampling selects source-video families before label-quality filtering.
Seven families have feature coverage inconsistent with source durations and one
has a zero-length source interval; those families are excluded without inventing
replacement labels. Retained descriptions and intervals are unchanged.
The final corpus has 742 videos and 902 training queries. Training videos are
separate from evaluation videos.

Native feature strides and source durations define the supplied time grids.
Original descriptions and fixed CLIP weights are supplied; raw videos and
precomputed query representations are not. The grid-attainable utility metric
with IoU thresholds 0.5, 0.7 and 0.9 is a task adaptation. Grid witnesses and
answer intervals remain verifier-only.

The current package has 5 public input rows and 450 held-out rows.

## Source terms

The [pinned Lighthouse repository](https://github.com/line/lighthouse/blob/3e841d3d662c8440afed514908566fed2d5e82a7/LICENSE) uses Apache 2.0. Retain Lighthouse, Charades-STA and ActivityNet Captions attribution for the supplied annotations and released features. The repository notice does not independently establish the usage terms of every underlying source video or derived feature; source-release coverage remains a maintainer review item. No raw video is distributed in this package. The selected families and time-grid adaptation are described above. CLIP's [original notice](https://github.com/openai/CLIP/blob/main/LICENSE) is MIT.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| openai/clip-vit-base-patch32 | model | 3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268 | 8 |
| search-swe/Search-SWE | dataset | 6df4714b27c7e5e24a01c4545725ee5475376aa7 | 1,489 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
