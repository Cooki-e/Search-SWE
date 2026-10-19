# Available Resources

The submission may use the external APIs below for retrieval and, where allowed by the task instruction, generative LLM calls.

The variables listed below are injected by Harbor at runtime and are available directly in your development processes. Read them as ordinary environment variables; for example, use `$OPENROUTER_API_KEY` in shell or `os.environ["JINA_API_KEY"]` in Python. Do not source a `.env` file inside the container. Only variables listed here and configured by Harbor are guaranteed to be available.

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

Credentials are runtime resources. Do not hard-code them, print or log their values, write them into code, memories, indexes, prompts or output artifacts, or assume they are available during Docker image build. Evaluation uses the stage-specific transports below; submitted processes do not receive provider keys.

Harbor restricts task API access to `openrouter.ai` and `api.jina.ai`. Documentation links are references and do not grant access to additional hosts.

```bash
OPENROUTER_API_KEY=<YOUR_OPENROUTER_API_KEY>
JINA_API_KEY=<YOUR_JINA_API_KEY>
```

## Retrieval resources

Embedding and reranking models may be used through Jina for memory preparation, index construction and retrieval. Use the exact model IDs and request formats supported by the selected Jina endpoint. These APIs are for text embedding and candidate scoring, not generation, external search, URL fetching or answer lookup. OpenRouter embedding and reranking endpoints are not supplied for this task. Local computation remains available without Jina.

Jina:

- Quickstart: `https://docs.jina.ai/get-started/quickstart`
- Embedding API documentation: `https://api.jina.ai/scalar#tag/search-foundation-models/POST/v1/embeddings`
- Reranking API documentation: `https://api.jina.ai/scalar#tag/search-foundation-models/POST/v1/rerank`
- Models: `https://jina.ai/models`

During development, use `JINA_API_KEY` with `https://api.jina.ai/v1/embeddings` or `https://api.jina.ai/v1/rerank`. Select a model supported by the corresponding endpoint; no single retrieval model is prescribed. Only text inputs are permitted.

During evaluation, `build.sh` and `run.sh` receive `TASK_JINA_CLIENT` and `TASK_JINA_FD` instead of a provider key. Load the supplied client module and use it for Jina requests:

```python
import importlib.util
import os

spec = importlib.util.spec_from_file_location("task_jina", os.environ["TASK_JINA_CLIENT"])
jina = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jina)
vectors = jina.embeddings(model=embedding_model_id, input=text_batch)
ranking = jina.rerank(model=reranker_model_id, query=question, documents=candidate_texts)
```

The client sends an operation (`embeddings` or `rerank`) and the provider request body through the supplied file descriptor. Preserve `TASK_JINA_FD` when starting subprocesses. Each serialized request, including its newline, must fit within 128 KiB; batch larger inputs. There is no separate Jina call-count limit, but calls count toward the build or retrieval time budget. Use only the current stage's permitted inputs. The answerer does not receive this transport, and direct network access from submitted evaluation processes is disabled.

## Generative LLM resources

Generative calls are allowed only through OpenRouter, and only from `answer.sh` using the current question and retrieved strings. The following four model IDs are the complete allowlist:

- `qwen/qwen3.6-35b-a3b` — `https://openrouter.ai/qwen/qwen3.6-35b-a3b`
- `qwen/qwen3.5-35b-a3b` — `https://openrouter.ai/qwen/qwen3.5-35b-a3b`
- `qwen/qwen3.5-9b` — `https://openrouter.ai/qwen/qwen3.5-9b`
- `qwen/qwen3-30b-a3b-instruct-2507` — `https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507`

The fourth ID is the exact OpenRouter identifier for `Qwen3-30B-A3B-Instruct-2507`. Include your chosen model ID in each request; you may select different allowed models within the question's call budget.

OpenRouter generation resources:

- Quickstart: `https://openrouter.ai/docs/quickstart`
- API documentation: `https://openrouter.ai/docs/api/reference/overview`
- OpenAI-compatible endpoint: `https://openrouter.ai/api/v1/chat/completions`

During evaluation, `answer.sh` receives `TASK_LLM_CLIENT` and `TASK_LLM_FD`. The supplied client forwards Chat Completions requests while retaining the provider credential outside the submitted process:

```python
import importlib.util
import os

spec = importlib.util.spec_from_file_location("task_llm", os.environ["TASK_LLM_CLIENT"])
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
response = api.chat_completion(
    messages=[{"role": "user", "content": prompt_from_current_question_and_retrieved_notes}],
    model="qwen/qwen3.5-9b",
    temperature=0,
    max_tokens=1000,
)
text = response["choices"][0]["message"]["content"]
```

The model in this example is one allowed choice. Preserve `TASK_LLM_FD` when starting subprocesses. When `TASK_LLM_CLIENT` is present, use the client without requiring `OPENROUTER_API_KEY` or direct network access. Without that transport during development, the answerer may send the same request body directly to the OpenRouter endpoint:

```python
import os
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
    json=request_body,
    timeout=45,
    allow_redirects=False,
)
response.raise_for_status()
result = response.json()
```

Build `request_body` only from the current question and retrieved notes, with an explicit allowed `model`. The answerer must not consult the full memory, index, original transcripts, previous requests or corpus-specific facts embedded in its code.

Each question permits at most two generation calls, each requesting 1–2,000 output tokens. The accepted options are `model`, `messages`, `temperature`, `top_p`, `max_tokens` and `response_format`. Messages must be a list of 1–32 objects with exactly the string fields `role` and `content`; allowed roles are `system`, `user` and `assistant`. Each serialized request, including its newline, must fit within 128 KiB. Streaming, tool calls and alternate endpoints are not supported. The same call and content restrictions apply to development self-tests.

### Strict allowlist and jailbreak penalty

The four model IDs, OpenRouter endpoint and answering-only use are mandatory restrictions. Do not call other generative models or providers, use generative APIs for memory preparation or retrieval, or use embedding and reranking endpoints as substitutes for generation. Only the listed Jina retrieval endpoints are permitted; external search, reader and answer services and benchmark-answer datasets are prohibited.

Do not seek unprovided evidence or reuse information across answering requests. A failed API call does not authorize an unlisted model, provider or endpoint. If the verifier or trajectory audit detects a prohibited call, access to hidden data or a bypass of the required pipeline, the entire task receives a score of `0`, regardless of retrieval or answer quality.
