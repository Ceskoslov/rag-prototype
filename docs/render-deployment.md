# Render + Neon + Upstash + Chroma Cloud

This deployment runs the FastAPI container and React static site on Render's
free plans while keeping state in managed services.

## 1. Create the managed services

### Neon

Create a free Neon project and copy its pooled or direct PostgreSQL connection
string. The application accepts Neon's standard `postgresql://` URL, including
`sslmode=require` and `channel_binding=require`; it converts these settings for
SQLAlchemy asyncpg automatically.

### Upstash

Create a free Redis database and copy the TLS connection string beginning with
`rediss://`. Redis stores parent chunks and ingestion file hashes. The Render
profile disables ARQ evaluation jobs because free Render plans do not support
background workers.

### Chroma Cloud

Create a Chroma Cloud database and record:

- API key
- tenant ID
- database name

The backend selects `chromadb.CloudClient` when `CHROMA_PROVIDER=cloud`.

### OpenAI

Create an API key. The Render profile uses OpenAI for generation and
embeddings so the 512 MB Render instance does not load a local transformer.
Hosted model and embedding calls are billed by OpenAI.

## 2. Create the Render Blueprint

In Render, select **New → Blueprint**, connect this repository, and select the
root `render.yaml`. The Blueprint creates:

- `universal-rag-api`: free Docker web service in Singapore
- `universal-rag-web`: free static React site

Enter these backend values when prompted:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Neon connection string |
| `REDIS_URL` | Upstash `rediss://` connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `CHROMA_TENANT` | Chroma tenant ID |
| `CHROMA_DATABASE` | Chroma database name |
| `CHROMA_API_KEY` | Chroma API key |
| `API_KEY` | A newly generated random value |

For the frontend, enter:

| Variable | Value |
| --- | --- |
| `VITE_API_BASE_URL` | `https://<api-service>.onrender.com/api/v1` |
| `VITE_API_KEY` | Exactly the same value as backend `API_KEY` |

`VITE_*` values are compiled into the static JavaScript bundle. Therefore the
API key is visible to browser users and should be treated as demo abuse
protection, not strong user authentication. A public production application
should replace it with per-user authentication.

## 3. First startup

The Render container:

1. runs `alembic upgrade head` against Neon;
2. scans `/data`;
3. embeds changed source files;
4. upserts vectors into Chroma Cloud;
5. stores parent chunks and file hashes in Upstash;
6. starts Uvicorn on Render's assigned `$PORT`.

Ingestion is deterministic. Later restarts skip unchanged files by their
SHA-256 hash. Set `INGEST_ON_STARTUP=false` after the first successful deploy
if startup ingestion is no longer desired.

## 4. Verify

```bash
curl https://<api-service>.onrender.com/api/v1/health

curl \
  -H "X-API-Key: <API_KEY>" \
  https://<api-service>.onrender.com/api/v1/knowledge-bases
```

Then open the static frontend and send a question.

## Free-tier constraints

- Render web services sleep after 15 minutes without traffic and have cold
  starts.
- Render's filesystem is ephemeral; the application does not store durable
  state there.
- Neon and Upstash scale down or pause under their free-plan policies.
- Chroma Cloud includes limited credits and then charges by usage.
- OpenAI API usage is not free.
- Free Render services do not support background workers, so evaluation
  endpoints are disabled by the Blueprint.

Do not commit any secret values. `render.yaml` uses `sync: false` for every
credential.
