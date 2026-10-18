# Available Resources

The optional APIs below are available through runtime environment variables `OPENROUTER_API_KEY` and `JINA_API_KEY`. Read these variables directly; do not source a `.env` file. Do not put credential values in code, indexes, outputs or logs.

Network access is limited to `openrouter.ai` and `api.jina.ai`. Documentation links do not permit access to other hosts.

## Retrieval resources

Embedding and reranking APIs may be used through OpenRouter or Jina. Use each provider's exact model IDs and request formats.

- [OpenRouter API documentation](https://openrouter.ai/docs/api_reference/overview)
- [OpenRouter embedding models](https://openrouter.ai/models?output_modalities=embeddings)
- [OpenRouter reranking models](https://openrouter.ai/models?output_modalities=rerank)
- [Jina embedding endpoint](https://api.jina.ai/scalar#tag/search-foundation-models/POST/v1/embeddings)
- [Jina reranking endpoint](https://api.jina.ai/scalar#tag/search-foundation-models/POST/v1/rerank)

## Generative resources

Generative calls may use only the OpenRouter endpoint `https://openrouter.ai/api/v1/chat/completions` and these model IDs:

- `qwen/qwen3.6-35b-a3b`
- `qwen/qwen3.5-35b-a3b`
- `qwen/qwen3.5-9b`

Other generative models, providers and endpoints are not permitted. Embedding and reranking endpoints may not be used as substitutes for generation. Use the supplied data; do not obtain external datasets, answer mappings or evaluation labels.

If a prohibited generative model, provider or endpoint is used, the submission is classified as a jailbreak and the entire task receives a score of zero.
