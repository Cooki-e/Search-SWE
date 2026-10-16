# Complete-set Graph Retrieval

## Task

Build an executable search system over the supplied knowledge graph. Return the complete set of matching node IDs for each question and maximize accuracy on held-out questions. Do not train or fine-tune models. The public examples are illustrative; support new combinations of relationships and conditions.

## Inputs and resources

- Corpus: `/task/data/corpus.sqlite`.
- Public validation questions: `/task/data/validation/queries.jsonl`.
- Public validation answers: `/task/data/validation/ground_truth.jsonl`.
- Installed software: `/task/docs/environment.md`.
- Permitted APIs and credential rules: `/task/docs/available_resources.md`.
- Resources: 16 CPUs, 32 GiB RAM, 100 GiB storage, no GPU; 120 minutes for implementation and validation.
- Use only the supplied corpus and permitted services. Hard-coded answers, hidden labels, external answer datasets and web search are prohibited.

## Submission

Create all submission files under `/app`; `/task` is read-only. Only `/app` transfers to a separate verifier. During verification, the program runs as a non-root user with `/app` read-only. Keep dependencies under `/app`, and indexes, caches and temporary files under the supplied `--index-dir`; honor `TMPDIR`.

Provide executable `/app/build.sh` and `/app/run.sh`.

## Build interface

The verifier builds once. The build must finish successfully within 1,800 seconds and may start a background service for queries.

```bash
/app/build.sh \
  --corpus /task/data/corpus.sqlite \
  --index-dir /path/to/index
```

## Query interface

The verifier invokes this command sequentially with one question per input file. Each invocation has a 30-second wall-clock limit and must exit successfully after writing its result.

```bash
/app/run.sh \
  --index-dir /path/to/index \
  --queries /path/to/queries.jsonl \
  --output /path/to/results.jsonl
```

## Output

Write one JSONL result per question, preserving its identifier and returning distinct integer node IDs.

```json
{"query_id":"query-id","answer_ids":[123,456]}
```

## Scoring

ExactSetAccuracy: each question earns 1 only for an exact match with the complete answer set, regardless of order. Wrong answers and timeouts earn 0. The displayed score is 100 times the average across all hidden questions.

A failed build, non-timeout execution failure, invalid output or failed compliance audit makes the entire submission score zero.
