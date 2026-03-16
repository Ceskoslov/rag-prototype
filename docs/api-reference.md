# API Reference

This document details the available endpoints for the SkyWing Airlines Multi-Agent RAG System. All endpoints are prefixed with `/api/v1`.

## Authentication

All endpoints, except `/health`, require an API key to be sent in the request header.

- **Header**: `X-API-Key: <your-api-key>`

The default API key is set via the `API_KEY` environment variable in your `.env` file.

---

## Chat Endpoints

### 1. POST /api/v1/chat

**Description**: Sends a message to the assistant and receives a full, non-streaming response. This is recommended for simple queries or environments where streaming is not supported.

**Headers**:
- `Content-Type: application/json`
- `X-API-Key: <your-api-key>`

**Request Body**:
```json
{
  "message": "What is the procedure for setting up VPN access?",
  "session_id": "session-123",
  "department": "it_support"
}
```
- `message` (string, required): The user's query.
- `session_id` (string, optional): A unique ID to maintain conversation history. If omitted, a new one will be generated.
- `department` (string, optional): One of `it_support`, `legal`, `credit_card`, `airport_ground`. If omitted, the Supervisor will automatically route the query.

**Response** (200 OK):
```json
{
  "answer": "To set up VPN access, you must first...",
  "session_id": "session-123",
  "department": "it_support",
  "sources": ["VPN_Setup_Guide.md", "Network_Policy.md"],
  "confidence": 0.92,
  "trace": {
    "supervisor_decision": "it_support",
    "agents_invoked": ["it_support"],
    "retrieval_sources": [
        {"title": "VPN_Setup_Guide.md", "snippet": "...", "department": "it_support"}
    ],
    "iterations": 1
  }
}
```

**Curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "How do I reset my password?",
    "session_id": "demo-001",
    "department": "it_support"
  }'
```

---

### 2. POST /api/v1/chat/stream

**Description**: Sends a message and receives tokens in real-time using Server-Sent Events (SSE).

**Headers**:
- `Content-Type: application/json`
- `X-API-Key: <your-api-key>`

**Request Body**:
Same as `POST /api/v1/chat`.

**Response** (200 OK, `text/event-stream`):
The response is a stream of events, each formatted as `data: {json}\n\n`.

**Event Types**:
- `heartbeat`: Periodic signal to keep the connection alive.
- `token`: Individual tokens of the assistant's answer.
- `sources`: List of documents retrieved for the answer.
- `trace`: Metadata about agent routing and confidence.
- `done`: Final event indicating the stream is complete.

**Curl Example**:
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "What are the baggage weight limits?",
    "session_id": "demo-002",
    "department": "airport_ground"
  }'
```

---

## Evaluation Endpoints

### 3. POST /api/v1/evaluation/trigger

**Description**: Triggers a background evaluation task for a specific conversation session using the RAGAS framework.

**Headers**:
- `Content-Type: application/json`
- `X-API-Key: <your-api-key>`

**Request Body**:
```json
{
  "session_id": "session-123"
}
```

**Response** (200 OK):
```json
{
  "job_id": "evaluation:session-123",
  "session_id": "session-123"
}
```

**Curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/evaluation/trigger \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "session_id": "demo-001"
  }'
```

---

### 4. GET /api/v1/evaluation/results/{session_id}

**Description**: Retrieves the RAGAS evaluation scores for a completed evaluation job.

**Headers**:
- `X-API-Key: <your-api-key>`

**Response** (200 OK):
```json
{
  "session_id": "session-123",
  "faithfulness": 0.95,
  "answer_relevancy": 0.88,
  "context_precision": 0.92,
  "context_recall": 0.85,
  "created_at": "2026-03-16T12:00:00Z"
}
```

---

### 5. GET /api/v1/evaluation/results/{session_id}/status

**Description**: Checks the current status of an evaluation job.

**Headers**:
- `X-API-Key: <your-api-key>`

**Response** (200 OK):
```json
{
  "session_id": "session-123",
  "status": "complete", // or "pending", "failed"
  "job_id": "evaluation:session-123"
}
```

---

## Health Check

### 6. GET /api/v1/health

**Description**: Checks the health status of the API and its backend dependencies (PostgreSQL, Redis, ChromaDB). This endpoint does **not** require an API key.

**Response** (200 OK):
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

**Curl Example**:
```bash
curl http://localhost:8000/api/v1/health
```
