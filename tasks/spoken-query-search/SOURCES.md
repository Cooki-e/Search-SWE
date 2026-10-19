# Sources and Preparation

This is package provenance for authors and reviewers. It is not mounted into
the agent environment; runtime resource permissions remain in the task instruction
and environment documentation.

## Dataset and preparation

The six original corpora, questions and qrels originate from
[SQuTR](https://huggingface.co/datasets/SLLMCommunity/SQuTR/tree/2f1b041e2e98e0d28ed68fbcf22126ef247eb719).
The supplied collection contains 8,292,040 original text documents.
Source audio is synthesized from questions and mixed with noise.

Fixed ASR inputs are an author adaptation using openai/whisper-small revision
973afd24965f72e36ca33b3055d56a652f456b4d: deterministic decoding alternatives,
conditional token probabilities and word-level aggregation. Clean reference
questions and qrels are not recognition inputs. Audio and ASR weights are not
runtime resources; no document vectors are supplied.

Five public question families retain clean/SNR20 variants. Their SNR0/SNR10
variants are unused; other families supply held-out rows across all four
conditions. Families never cross the split. Mean nDCG@10 equally weights
collections and acoustic conditions; this does not establish speaker-disjoint
generalization.

The current package has 10 public input rows and 4,550 held-out rows.
Multiple versions of one original question stay in the same split; public
input-row counts therefore exceed the five public question families.

## Source terms

The [pinned SQuTR dataset card](https://huggingface.co/datasets/SLLMCommunity/SQuTR/blob/2f1b041e2e98e0d28ed68fbcf22126ef247eb719/README.md) declares CC BY-SA 4.0. Preserve SQuTR attribution and the applicable notices of its six source collections. The noisy recognition alternatives are this task's disclosed preparation, not original human transcripts. Multilingual E5-small is MIT at its fixed model revision. Whisper was a preparation-only tool and is not delivered as a runtime resource.

## Runtime asset sources

| Repository | Type | Immutable revision | Files |
| --- | --- | --- | ---: |
| intfloat/multilingual-e5-small | model | 614241f622f53c4eeff9890bdc4f31cfecc418b3 | 8 |
| search-swe/Search-SWE | dataset | dc952fbffa3c3325db82cc07d7727a7ed868f78e | 8 |

The manifest records exact task-relative paths and asset bytes. Source pins do
not change the corpus, examples, labels or model weights. Original upstream
source and model notices continue to apply.
