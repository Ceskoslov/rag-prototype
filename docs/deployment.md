# Deployment guide

## Prerequisites

- Docker Engine with Docker Compose v2
- An OpenAI or Azure OpenAI key for real generation; `LLM_PROVIDER=mock` is
  sufficient only for infrastructure checks
- Enough memory for the chosen local embedding model

## Configure

```bash
cp .env.example .env
```

At minimum, replace `API_KEY`. For OpenAI set:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-luna
```

The default embedding configuration is local multilingual `BAAI/bge-m3`.
OpenAI and Azure embedding providers are also supported. If the embedding model
changes after indexing, rebuild the affected collections.

Add documents under first-level directories:

```text
data/
  company_policies/
    handbook.pdf
  product_docs/
    api.md
```

Directory names are normalized into safe knowledge-base slugs.

## Start and index

```bash
docker compose up -d --build
docker compose ps
docker compose exec api python scripts/ingest.py --all --data-dir /data
```

The stack includes PostgreSQL 16, Redis 8.1, Chroma 1.5.9, FastAPI, an ARQ
worker, the React frontend, and Nginx. The one-shot `seed` service also indexes
all directories under `/data` during startup.

Access points:

- UI through Nginx: `http://localhost`
- Frontend development port: `http://localhost:3000`
- API: `http://localhost:8000`
- OpenAPI UI: `http://localhost:8000/docs`
- Chroma host port: `http://localhost:8001`

## Verify

```bash
curl http://localhost:8000/api/v1/health
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/knowledge-bases
docker compose logs seed
```

## Operations

Follow logs:

```bash
docker compose logs -f api worker
```

Re-index after document updates:

```bash
docker compose exec api python scripts/ingest.py --all --data-dir /data
```

Stable chunk IDs and Chroma upserts make this repeatable. A source's previous
chunks are removed before its current contents are indexed.

Back up the `postgres_data`, `redis_data`, and `chroma_data` named volumes.
Configure real TLS certificates and stricter network/access controls before
internet exposure. Keep the API key outside source control.

To intentionally erase all indexed knowledge and conversation data:

```bash
docker compose down -v
```

This action is destructive and cannot be reversed without backups.
