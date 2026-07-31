# Universal RAG

A domain-agnostic retrieval-augmented generation starter. Point it at folders of
documents and it exposes a cited chat API and web UI—without adding a new agent
or enum for every business domain.

## What changed from the original prototype

- Knowledge bases are discovered dynamically from `data/<name>/`; the fixed
  airline department router and multi-agent supervisor are gone.
- Omitting `knowledge_base` searches across every indexed collection.
- Dense and BM25 results are fused with reciprocal-rank fusion.
- The configured embedding model is now used explicitly for both ingestion and
  queries. The original implementation instantiated an embedding model but let
  Chroma silently use its own default.
- Markdown, text, reStructuredText, HTML, JSON, CSV, and PDF files are supported.
- Deterministic chunk IDs plus Chroma `upsert` make re-indexing repeatable.
- Retrieved text is treated as untrusted data and answers cite numbered sources.
- LangGraph, LangChain integrations, Chroma, FastAPI, Redis, Ragas, and build
  tooling are updated to their current major APIs and pinned versions.
- OpenAI calls use the Responses API; Azure OpenAI and a no-network mock mode
  remain available.

## Architecture

```mermaid
flowchart LR
    A["Folders under data/"] --> B["Format-aware loader"]
    B --> C["Parent/child chunking"]
    C --> D["Configured embedding model"]
    D --> E["Chroma collections"]
    C --> F["Redis parent store"]
    Q["User question"] --> G["Dense + BM25 retrieval"]
    E --> G
    F --> G
    G --> H["Self-correcting RAG graph"]
    H --> I["Grounded answer + citations + trace"]
```

The graph uses a bounded retrieve → generate → critique loop. It rewrites and
retrieves again only when the answer is rejected, so latency is predictable and
there is no agent-to-agent routing overhead.

## Quick start

1. Copy the environment template and set credentials:

   ```bash
   cp .env.example .env
   ```

2. Add documents. Each first-level directory is one knowledge base:

   ```text
   data/
     product_docs/
       getting-started.md
       api.pdf
     policies/
       refunds.txt
   ```

3. Start infrastructure and applications:

   ```bash
   docker compose up --build
   ```

4. Index every discovered knowledge base:

   ```bash
   docker compose exec api python scripts/ingest.py --all --data-dir /data
   ```

5. Open `http://localhost:3000`.

The default `LLM_PROVIDER=mock` is useful for wiring checks but does not generate
real answers. Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`, or configure the
Azure variables, for actual generation.

## Deploy on Render

The repository includes `render.yaml` for a free Render web service and static
site backed by Neon Postgres, Upstash Redis, and Chroma Cloud. See
[`docs/render-deployment.md`](docs/render-deployment.md) for account setup,
secret values, deployment order, and free-tier limitations.

## API

List indexed knowledge bases:

```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/knowledge-bases
```

Query a specific knowledge base:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message":"What is the refund window?","knowledge_base":"policies"}'
```

Search all knowledge bases by omitting the optional field:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"message":"What changed in the latest release?"}'
```

For SSE, use `POST /api/v1/chat/stream` with the same request body.

## Local development

Backend:

```bash
cd apps/backend
uv sync
uv run pytest
uv run ruff check app tests
```

Frontend:

```bash
cd apps/frontend
npm ci
npm test
npm run build
```

## Operational notes

- Changing `EMBEDDING_PROVIDER` or `EMBEDDING_MODEL_NAME` requires rebuilding
  the affected collections; embedding spaces are not interchangeable.
- `BAAI/bge-m3` is the default local multilingual model. It is larger than the
  old English-only model; choose a smaller model if memory is constrained.
- Chroma is pinned rather than using `latest`, stores data at `/data`, and uses
  the current `/api/v2/heartbeat` health check.
- The database column named `department` is retained for conversation migration
  compatibility; it now stores a knowledge-base slug or `all`.

## License

See the repository license, if present.
