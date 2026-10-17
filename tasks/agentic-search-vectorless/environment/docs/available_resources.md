# Available Resources

The submission may use the external API below for permitted generative LLM calls only.

The variables listed below are injected by Harbor at runtime and are available directly in the agent container's process environment, including child processes started by the agent. Read them as ordinary environment variables; for example, use `$OPENROUTER_API_KEY` in shell or `os.environ["OPENROUTER_API_KEY"]` in Python. Do not source a `.env` file inside the container. Only variables listed in this document and configured by Harbor are guaranteed to be available. Do not assume that all variables from a `.env` file are automatically injected.

For example, check whether a credential is present without exposing its value:

```bash
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "OPENROUTER_API_KEY is not set" >&2
    exit 1
fi
```

```python
import os

if not os.environ.get("OPENROUTER_API_KEY"):
    raise RuntimeError("OPENROUTER_API_KEY is not set")
```

These credentials are runtime resources. Do not hard-code them, print or log their values, write them into source code, indexes, or output artifacts, or assume that they are available during Docker image build.

Harbor restricts runtime egress to `openrouter.ai`. Documentation links below do not grant
access to any additional host. The coding agent's own phase-scoped model host
is not a submission resource.

```bash
OPENROUTER_API_KEY=<YOUR_OPENROUTER_API_KEY>
```

## Retrieval resources

Embeddings (local, API, or precomputed), BM25 and its variants, and external retrieval/reranking services are prohibited. The OpenRouter key is for the permitted generative models only, not retrieval endpoints. The task does not prescribe a retrieval implementation or programming language.

## Generative LLM resources

Generative calls are allowed only through the OpenRouter API. The following four model IDs are the complete allowlist:

- `qwen/qwen3.6-35b-a3b` — `https://openrouter.ai/qwen/qwen3.6-35b-a3b`
- `qwen/qwen3.5-35b-a3b` — `https://openrouter.ai/qwen/qwen3.5-35b-a3b`
- `qwen/qwen3.5-9b` — `https://openrouter.ai/qwen/qwen3.5-9b`
- `qwen/qwen3-30b-a3b-instruct-2507` — `https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507`

The fourth model ID above is the exact OpenRouter identifier corresponding to the `Qwen3-30B-A3B-Instruct-2507` model name.

OpenRouter generation resources:

- Quickstart: `https://openrouter.ai/docs/quickstart`
- API documentation: `https://openrouter.ai/docs/api_reference/overview`
- PDF OCR / multimodal PDF guide: `https://openrouter.ai/docs/guides/overview/multimodal/pdfs`
- OpenAI-compatible endpoint: `https://openrouter.ai/api/v1/chat/completions`

### Strict allowlist and jailbreak penalty

The four Qwen IDs above are an allowlist, not a recommendation. Do not call any other generative model ID, any other generative provider, or a prohibited chat/completions endpoint. In particular, do not use another provider's generative endpoint or an embedding/reranking endpoint.

If the verifier or trajectory audit detects a prohibited generative model or provider call, the submission is classified as jailbreak and the entire task receives a score of `0`, regardless of retrieval quality or final answer quality.

The mandatory verifier-only audit also checks the embedding/BM25 bans, the
20-round retrieval limit, hidden-label access and verifier manipulation.
Violations zero the entire reward. Audit credentials and the DeepSeek judge
endpoint are verifier resources only, not available to submitted commands.
