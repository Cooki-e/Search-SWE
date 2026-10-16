I need to answer business questions using data spread across several databases. I have a catalog of their tables, but I need to find which tables belong together and which columns connect them before writing a SQL query. Please build an executable search engine that takes a natural-language question and returns five candidate tables with up to six joins. The goal is to retrieve a complete set of tables and relationships that can support the question. Choose the indexing and retrieval approach; generating or executing SQL is outside this task.

Before choosing your approach, read `/task/docs/environment.md` and `/task/docs/available_resources.md`. They describe the installed runtime and the permitted retrieval and generative APIs, including model allowlists, providers, endpoints, credential handling and jailbreak penalties. You may use the documented embedding and reranking APIs during indexing and querying, and the permitted generative models for query interpretation, candidate selection and join reasoning. Follow those resource restrictions. Harbor injects the documented credentials at runtime; do not include credentials in submission files or generated artifacts.

The catalog to search is `/task/data/catalog.json`, a JSON object containing `schema_version`, `tables` and `joins`. Each table has an opaque `table_id` and database `group_id`, its original name and description, column definitions, a row count and sample rows. Columns have IDs scoped to their table, original names, types and primary-key metadata. If several columns have `primary_key: true`, they jointly form the table's primary key. Samples are incomplete and are supplied to help interpret the data. The public `joins` list defines the available column-level equality relationships. Questions do not identify their database group, so the engine must search the shared catalog. You can inspect and index the entire catalog before queries arrive.

Public development questions are in `/task/data/validation/queries.jsonl`, with reference labels in `/task/data/validation/labels.jsonl`. Each label contains `query_id` and `acceptable_plans`, whose entries have `table_ids` and `joins`. Use these examples to develop and check real retrieval from the catalog. Implement any local validation checks you need using these labels and the scoring rule below. Do not hard-code question-specific answers, obtain external Spider SQL or answers, inspect hidden grading files, or manipulate grading or reward files. Full databases and source SQL are not supplied. Final evaluation uses held-out questions and labels that are not copied into your environment.

Put the implementation and all supporting files in `/app/submission`, which starts empty. The final submission must include working `build.sh` and `search.sh` entrypoints. Harbor transfers only this directory to a fresh verifier, where submission commands run as an unprivileged user. Package any additional dependencies there; globally installed changes, development indexes and running processes do not transfer.

To prepare the catalog for search, the verifier invokes:

```bash
bash /app/submission/build.sh \
  --corpus /task/data/catalog.json \
  --index-dir /work/index
```

The supplied index directory exists and is empty. Build all index files under that path and return exit status 0 when ready, within 1,200 seconds. The index may contain only regular files and directories totaling at most 8 GiB. The verifier builds once before sending queries.

After a successful build, it starts the search process with:

```bash
bash /app/submission/search.sh \
  --index-dir /work/index
```

Print `{"ready":true}` followed by a newline within 30 seconds, then keep the process alive to read one JSON query per stdin line until EOF. Each query contains exactly `query_id` and `question`, for example:

```json
{"query_id":"opaque-query-id","question":"A natural-language business question."}
```

For each query, emit and flush one JSON response on stdout within 20 seconds of receiving it. Send diagnostics to stderr. API calls count toward the applicable build, readiness or query deadline. Query IDs and ordering may change; preserve the received ID without interpreting it. An unscored warm-up query precedes evaluation. If warm-up fails, the verifier may restart the process before sending a scored query; warm-up failure itself does not reduce a query's score.

Each response contains exactly `query_id`, `table_ids` and `joins`. Its structure is illustrated below with placeholder IDs; use real catalog IDs and relationships in your output. The example is expanded for readability, but emit each response as a single JSON line, at most 65,536 bytes including its newline.

```json
{
  "query_id": "opaque-query-id",
  "table_ids": ["tbl_A", "tbl_B", "tbl_C", "tbl_D", "tbl_E"],
  "joins": [
    {
      "left_table": "tbl_A",
      "left_column": "c_000",
      "right_table": "tbl_B",
      "right_column": "c_001"
    }
  ]
}
```

Return exactly five distinct table IDs and zero to six distinct public joins. Each join must have exactly the four fields shown, refer to returned tables and identify real columns of those tables. Do not invent cross-group relationships. Table order, join order and reversing both endpoints of a join do not affect scoring. Extra legal candidates within the budgets are allowed; the full candidate set need not be connected or belong to one database group.

During final evaluation, a question earns 1 only when a valid response contains every table and every join of the same acceptable plan, and 0 otherwise. The reward is the mean across all evaluation questions, including failures, with no partial credit. Missing, late or malformed responses, duplicate JSON keys, duplicate tables or joins, extra fields, and unknown or invalid identifiers or relationships fail that question. A failed search process may be restarted for subsequent questions; a build failure or index-limit violation gives zero overall. Only complete table-and-join coverage contributes to the reward.
