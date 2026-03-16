# Deployment Guide

This guide provides instructions for deploying the SkyWing Airlines Multi-Agent RAG System using Docker Compose.

## Prerequisites

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+ (included in Docker Desktop)
- **OpenAI API Key** (Optional): If using Azure OpenAI for embeddings or LLM, though the system defaults to local `bge-base-en-v1.5` embeddings.

## Configuration

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set up environment variables**:
   Copy the example environment file and edit it with your credentials:
   ```bash
   cp .env.example .env
   ```
   Key variables to configure:
   - `API_KEY`: The key used for authenticating with your FastAPI backend.
   - `AZURE_OPENAI_API_KEY`: (If using Azure OpenAI)
   - `AZURE_OPENAI_ENDPOINT`: (If using Azure OpenAI)
   - `EMBEDDING_PROVIDER`: Set to `local` (default) or `azure`.

## Deployment Steps

1. **Start all services**:
   ```bash
   docker compose up -d
   ```
   This will build the backend and frontend images, and start 8 services:
   - `postgres`: PostgreSQL 16 (Relational DB + Checkpoints)
   - `redis`: Redis 7 (Caching + Background job queue)
   - `chromadb`: ChromaDB (Vector Store)
   - `api`: FastAPI Backend
   - `worker`: ARQ Background Worker
   - `seed`: Data Seeding Service (Runs once to ingest documents)
   - `frontend`: React TypeScript Frontend
   - `nginx`: Reverse Proxy

2. **Verify service health**:
   Check the status of all containers:
   ```bash
   docker compose ps
   ```
   Wait until all services show `(healthy)` (especially `postgres`, `redis`, and `chromadb`).

3. **Check Seeding Status**:
   The `seed` container will automatically ingest the synthetic airline documents into ChromaDB. Verify it completed successfully:
   ```bash
   docker compose logs seed
   ```
   You should see messages indicating that documents were processed and stored.

## Accessing the System

- **Frontend UI**: [http://localhost](http://localhost) (via Nginx on port 80)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Direct API Access**: Port 8000 (e.g., `http://localhost:8000/api/v1/health`)

## Service Port Mappings

| Service | Internal Port | External Port | Description |
|---|---|---|---|
| Nginx | 80 / 443 | 80 / 443 | Main entry point |
| FastAPI | 8000 | 8000 | Backend API |
| Frontend | 5173 | 3000 | Vite dev server |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache / Queue |
| ChromaDB | 8000 | 8001 | Vector Database |

## Troubleshooting

### Checking Logs
To view logs for a specific service (e.g., the API):
```bash
docker compose logs -f api
```

### Restarting Services
If a service is behaving unexpectedly:
```bash
docker compose restart api
```

### Clean Re-deployment
If you need to wipe all data and start fresh (CAUTION: this deletes all conversation history and ingested knowledge):
```bash
docker compose down -v
docker compose up -d --build
```

### SSE Connection Issues
If you experience issues with real-time streaming, ensure Nginx is correctly configured (the provided `nginx.conf` handles this by disabling `proxy_buffering`). You can check Nginx logs:
```bash
docker compose logs nginx
```

## Production Considerations

- **API Key**: Always change the default `API_KEY` in `.env` for production deployments.
- **Persistence**: Data is persisted using Docker volumes (`postgres_data`, `redis_data`, `chroma_data`). Ensure these are backed up periodically.
- **Nginx SSL**: For production, update the `nginx/ssl` directory with valid certificates and update `nginx.conf` to enforce HTTPS.
- **Resource Limits**: In a production environment, consider adding `deploy.resources.limits` to the `docker-compose.yml` for memory and CPU management.
