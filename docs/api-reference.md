# API reference

Every endpoint is prefixed with `/api/v1`. Except for `/health`, requests need
the header `X-API-Key: <your-api-key>`.

Interactive OpenAPI documentation is available at `/docs`.

## `GET /api/v1/knowledge-bases`

Returns knowledge bases discovered in Chroma and their child-chunk counts.

```json
[
  {"name": "company_policies", "document_chunks": 42},
  {"name": "product_docs", "document_chunks": 87}
]
```

## `POST /api/v1/chat`

`knowledge_base` is optional. Omit it to search all indexed knowledge bases.
The old input name `department` is accepted temporarily as a validation alias.

```json
{
  "message": "What is the refund window?",
  "knowledge_base": "company_policies",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "answer": "The refund window is 30 days [1].",
  "knowledge_bases": ["company_policies"],
  "sources": ["refunds.md"],
  "confidence": 0.9,
  "trace": {
    "knowledge_bases_searched": ["company_policies"],
    "retrieval_sources": [
      {
        "title": "refunds.md",
        "snippet": "Refunds are available for 30 days.",
        "knowledge_base": "company_policies"
      }
    ],
    "iterations": 1,
    "pipeline_steps": ["retrieve", "generate", "critique"]
  },
  "session_id": "optional-session-id"
}
```

Example:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message":"What changed in the latest release?"}'
```

## `POST /api/v1/chat/stream`

Accepts the same request as `/chat` and returns `text/event-stream`. Events are
JSON in `data: ...` frames:

- `heartbeat`
- `token` with a `content` field
- `sources`
- `trace`
- `error` when generation fails
- `done`

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message":"Summarize the onboarding guide.","knowledge_base":"product_docs"}'
```

## Evaluation

`POST /api/v1/evaluation/trigger` queues evaluation for an existing session:

```json
{"session_id": "optional-session-id"}
```

`GET /api/v1/evaluation/results/{session_id}/status` returns `pending`,
`complete`, or `failed`. `GET /api/v1/evaluation/results/{session_id}` returns
faithfulness, answer relevancy, context precision, and context recall scores.

## `GET /api/v1/health`

Does not require an API key.

```json
{
  "status": "ok",
  "services": {
    "redis": "ok",
    "chromadb": "ok",
    "postgres": "ok"
  }
}
```
