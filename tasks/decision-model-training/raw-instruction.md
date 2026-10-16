# Decision Model Training

## Task

Build a local decision model based on Qwen3-0.6B. Given a text or JSON state and
the questions and answer menus for a request, return the appropriate decisions.
Handle categorical choices, Boolean decisions, and ordinal ratings, including
task schemas absent from the supplied examples.

## Resources and restrictions

- Read `/task/docs/environment.md` and `/task/docs/available_resources.md`.
- Labeled examples: `/task/data/examples.jsonl`.
- Starting model: `/task/models/Qwen3-0.6B`.
- `/task` is read-only. Network access and external APIs are unavailable. Do not
  use external datasets, additional pretrained weights, hidden examples or
  labels, precomputed answers, or hard-coded input-to-answer mappings.
- Development budget: 6 hours; one NVIDIA A100 40GB, 16 CPU cores, 32 GiB RAM,
  100 GiB storage.

## Submission and execution

Submit all runtime files under `/app/submission`, including executable
`start.sh` and `run.sh`. Only this directory is transferred. Installed packages
and running processes from development are not transferred. The separate
verifier retains the model and resource documents but not `examples.jsonl`.
The submission runs as a non-root user with `/app/submission` read-only. Write
runtime files under the supplied `--runtime-dir` and results to `--output`.

```bash
/app/submission/start.sh --runtime-dir /path/to/runtime
```

The initially empty runtime directory may vary. Finish model loading and
initialization and return exit status zero within 120 seconds. Resident
processes can remain available for the following call. No hidden requests are
available before startup completes.

```bash
/app/submission/run.sh \
  --runtime-dir /path/to/runtime \
  --requests /path/to/requests.jsonl \
  --output /path/to/results.jsonl
```

Input JSONL records contain `request_id`, `state`, and `questions`, using the
same question format as the examples. Output one JSONL record per request:
`{"request_id":"request-id","answers":{"question-id":"selected-label"}}`.
Return every question's answer exactly once: `choice` is an exact criterion key
string, `noul` a JSON Boolean, and `score` an integer indexing the ordered
criteria list from zero. Cover every request exactly once; output order is free.

The complete batch of 4,200 requests has a 240-second limit after startup.
Input processing, inference and output writing count toward this limit.
Batching is allowed. Return exit status zero after the complete output is written.

## Evaluation

Hidden evaluation uses exact answer accuracy, averaged over seven equally sized
datasets. Maximize this accuracy. Startup or inference timeout, command failure,
missing or invalid output, or an integrity violation results in score zero.
