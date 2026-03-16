# Multi-Agent Agentic RAG — Enterprise Airline Knowledge System

## TL;DR

> **Quick Summary**: Build a near-production-grade portfolio project demonstrating a multi-agent system with Agentic RAG for a large airline's enterprise knowledge retrieval. 4 department agents (IT Support, Legal, Credit Card, Airport Ground Services) orchestrated by a Supervisor agent, each backed by hybrid search (BM25 + Vector) with Self-RAG quality refinement.
> 
> **Deliverables**:
> - FastAPI backend with LangGraph multi-agent system (1 Supervisor + 4 Department agents)
> - Self-RAG pipeline per agent (retrieve → generate → critique → refine, max 3 iterations)
> - Hybrid search (BM25 + Vector via EnsembleRetriever with RRF) per department
> - Parent-Child chunking with Redis-backed persistent docstore
> - SSE streaming for real-time chat responses
> - React + TypeScript frontend (chat UI + department selector + agent trace panel)
> - Docker Compose deployment (API + Worker + Redis + ChromaDB + PostgreSQL + Nginx + Frontend)
> - RAGAS evaluation via background jobs (ARQ)
> - Synthetic airline documents for all 4 departments
> - Comprehensive README with architecture diagrams
> - Full TDD: pytest (backend) + Vitest (frontend)
> 
> **Estimated Effort**: Large (4-6 weeks)
> **Parallel Execution**: YES — 5 waves
> **Critical Path**: Scaffolding → Embedding/VectorStore → Chunking/Retrieval → Self-RAG Graph → Department Agents → Supervisor → Chat API + SSE → Frontend → Docker → Docs

---

## Context

### Original Request
User is preparing to apply for an **AI Agent Engineer** position. Their resume describes an enterprise multi-agent + RAG system (toB) built with Microsoft Autogen + Semantic Kernel + Azure, but since it's company IP, they need a personal portfolio version using a different tech stack (LangChain + LangGraph). The project simulates a large airline company with multi-department knowledge retrieval.

### Interview Summary
**Key Discussions**:
- **Departments**: IT Support, Legal, Credit Card Division, Airport Ground Services (large airline)
- **Cross-department**: Mixed mode — default isolated, Supervisor can trigger cross-department retrieval when needed
- **Embedding**: Dual mode — local bge-base-en-v1.5 (default) switchable to Azure OpenAI via env var
- **Vector DB**: Chroma only (dropped Milvus abstraction per Metis recommendation)
- **Database**: PostgreSQL added for conversation persistence, LangGraph checkpointing, RAGAS results
- **Auth**: Simple API key header (X-API-Key)
- **Frontend**: Single page — chat UI + department selector + collapsible agent trace panel
- **Streaming**: SSE (not WebSocket) — simpler, auto-reconnection, works through proxies
- **Testing**: TDD with pytest (backend), Vitest (frontend unit only)
- **Docs**: Clear and detailed (portfolio quality)

**Research Findings**:
- LangGraph Supervisor (`create_supervisor` from `langgraph-supervisor` package) + `create_react_agent` is the official recommended pattern
- Self-RAG with `RemainingSteps` managed value for iteration control (max 3 iterations)
- EnsembleRetriever (BM25 + Vector with RRF) improves recall 12-18% over vector-only
- Parent-Child chunking: small chunks (200 tokens) for precise retrieval, parent chunks (1000 tokens) for context
- `ParentDocumentRetriever` default `InMemoryStore` is ephemeral — MUST use Redis-backed docstore
- ARQ preferred over Celery for async-first FastAPI systems
- bge-base-en-v1.5 achieves 95% of Azure OpenAI embedding quality at zero cost
- SSE with `StreamingResponse(media_type="text/event-stream")` — ChatGPT itself uses SSE
- ChromaDB: use `HttpClient` for multi-container Docker setup, batch inserts via `create_batches`
- Nginx needs `proxy_buffering off` + `proxy_read_timeout 300s` for SSE

### Metis Review
**Identified Gaps** (all resolved):
- ParentDocumentRetriever persistence → Redis-backed docstore
- Azure OpenAI rate limiting with concurrent agents → exponential backoff with `tenacity`
- ChromaDB concurrent write safety → queue writes through single ARQ worker
- SSE timeout through Nginx → `proxy_buffering off`, `proxy_read_timeout 300s`, heartbeat events
- BM25Retriever memory usage → lazy initialization per-department
- Local embedding model download on first run → pre-download in Dockerfile
- `langchain_classic` namespace migration → pin exact versions, verify imports
- Self-RAG infinite loop → `RemainingSteps` + `recursion_limit` + hard cap at 3 iterations

---

## Work Objectives

### Core Objective
Build a near-production-grade multi-agent + Agentic RAG system that demonstrates technical depth for AI Agent Engineer interviews, using LangGraph for agent orchestration and FastAPI for the backend.

### Concrete Deliverables
- `apps/backend/` — FastAPI backend with LangGraph agents, RAG pipeline, SSE streaming
- `apps/frontend/` — React + TypeScript chat UI with department selector + agent trace panel
- `apps/worker/` — ARQ worker for background tasks (document ingestion, RAGAS evaluation)
- `docker-compose.yml` — Full deployment stack
- `docs/` — Architecture diagrams, API reference, setup guide
- `scripts/` — CLI tools for document ingestion, evaluation triggers
- Synthetic airline documents for 4 departments

### Definition of Done
- [ ] `docker compose up` starts all 8 services (api, worker, redis, chromadb, postgres, nginx, frontend, seed)
- [ ] All services pass health checks within 60 seconds
- [ ] Chat query to IT Support returns relevant answer with citations from IT knowledge base
- [ ] Cross-department query invokes multiple agents and merges responses
- [ ] SSE stream delivers tokens incrementally (not batched)
- [ ] Agent trace panel shows routing decision + retrieval sources
- [ ] `pytest` passes with 0 failures
- [ ] `vitest run` passes with 0 failures
- [ ] RAGAS evaluation endpoint triggers and returns metrics
- [ ] README is comprehensive with architecture diagram, setup guide, and demo walkthrough

### Must Have
- LangGraph Supervisor pattern (`create_supervisor` + `create_react_agent`)
- Self-RAG with critique loop (max 3 iterations, `RemainingSteps`)
- Hybrid search (BM25 + Vector with RRF) per department
- Parent-Child chunking with Redis-backed persistent docstore
- Dual embedding mode (local bge-base-en-v1.5 / Azure OpenAI via env var)
- SSE streaming for chat responses
- Docker Compose deployment with health checks
- TDD: pytest + Vitest
- Structured logging with `structlog`
- API key authentication (X-API-Key header)
- PostgreSQL for conversation history + LangGraph checkpoints + RAGAS results
- Exponential backoff for Azure OpenAI calls (`tenacity`)
- Per-agent timeout (30s) via `asyncio.wait_for`

### Must NOT Have (Guardrails)
- ❌ Vector DB abstraction layer — Chroma only, no Milvus interface
- ❌ `langchain` meta-package — use `langchain-core`, `langchain-openai`, `langchain-community`, `langgraph`, `langgraph-supervisor`
- ❌ `InMemoryStore` for parent document persistence — use Redis-backed store
- ❌ Concurrent ChromaDB writes — queue through single ARQ worker
- ❌ User management system — no registration, login, user profiles
- ❌ CI/CD pipelines — no GitHub Actions, Kubernetes, Terraform
- ❌ Frontend pages beyond chat + trace panel — no admin dashboard, analytics
- ❌ Document upload UI — ingestion via CLI scripts / API endpoints only
- ❌ Model management UI — Azure OpenAI config via `.env` only
- ❌ Semantic caching in Redis
- ❌ Real-time collaboration / multi-user WebSocket rooms
- ❌ E2E browser tests (Playwright/Cypress)
- ❌ OCR / table extraction for document processing
- ❌ Floating dependency versions — pin all exact versions
- ❌ `as any` / `@ts-ignore` in TypeScript code
- ❌ Empty catch blocks, console.log in production code
- ❌ Over-abstraction, excessive comments, generic variable names (data/result/item/temp)

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.
> Acceptance criteria requiring "user manually tests/confirms" are FORBIDDEN.

### Test Decision
- **Infrastructure exists**: NO (greenfield)
- **Automated tests**: TDD (RED → GREEN → REFACTOR)
- **Backend framework**: pytest + pytest-asyncio + httpx (async test client)
- **Frontend framework**: Vitest + React Testing Library
- **If TDD**: Each task writes failing tests FIRST, then implements to make them pass

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API/Backend**: Use Bash (curl) — Send requests, assert status + response fields
- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **Agent Logic**: Use Bash (python/pytest) — Run agent graph, verify output structure
- **Docker**: Use Bash (docker compose) — Verify services, health checks, logs

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — Start Immediately, 7 parallel):
├── Task 1: Monorepo scaffolding + config files [quick]
├── Task 2: Backend core settings + structured logging [quick]
├── Task 3: Pydantic schemas + type definitions [quick]
├── Task 4: Docker Compose skeleton + service configs [quick]
├── Task 5: Frontend scaffolding (Vite + React + shadcn/ui + Zustand) [quick]
├── Task 6: Synthetic airline documents for 4 departments [writing]
└── Task 7: PostgreSQL models + Alembic migrations [quick]

Wave 2 (Core RAG Pipeline — After Wave 1, 6 parallel):
├── Task 8: Dual embedding factory (bge-base-en-v1.5 / Azure) [deep] (depends: 2, 3)
├── Task 9: ChromaDB repository + batch operations [deep] (depends: 2, 3)
├── Task 10: Redis-backed docstore for parent documents [unspecified-high] (depends: 2)
├── Task 11: Document chunking pipeline (Parent-Child + RecursiveCharacter) [deep] (depends: 3)
├── Task 12: API key auth middleware + health endpoints [quick] (depends: 2)
└── Task 13: Conversation repository (PostgreSQL CRUD) [unspecified-high] (depends: 7)

Wave 3 (Agents + Retrieval — After Wave 2, 6 parallel):
├── Task 14: Hybrid retriever (BM25 + Vector EnsembleRetriever) [deep] (depends: 8, 9, 10, 11)
├── Task 15: Self-RAG StateGraph with critique loop [ultrabrain] (depends: 8, 14)
├── Task 16: Document ingestion service + CLI script [unspecified-high] (depends: 6, 9, 10, 11)
├── Task 17: Department agent factory (create_react_agent × 4) [deep] (depends: 14, 15)
├── Task 18: Frontend chat UI components [visual-engineering] (depends: 5)
└── Task 19: Frontend Zustand stores + SSE hook [quick] (depends: 5)

Wave 4 (Integration — After Wave 3, 6 parallel):
├── Task 20: Supervisor agent (create_supervisor) [deep] (depends: 17)
├── Task 21: Chat service + SSE streaming API [deep] (depends: 12, 13, 15, 20)
├── Task 22: Frontend chat page assembly + agent trace panel [visual-engineering] (depends: 18, 19)
├── Task 23: ARQ worker setup + background tasks [unspecified-high] (depends: 2, 9)
├── Task 24: RAGAS evaluation service + endpoint [deep] (depends: 13, 23)
└── Task 25: Seed data ingestion via ARQ [unspecified-high] (depends: 16, 23)

Wave 5 (Production Polish — After Wave 4, 5 parallel):
├── Task 26: Docker Compose production config + Nginx SSE [unspecified-high] (depends: 4, 21, 22, 25)
├── Task 27: Frontend ↔ Backend integration + SSE wiring [visual-engineering] (depends: 21, 22)
├── Task 28: LangGraph checkpointing with AsyncPostgresSaver [unspecified-high] (depends: 7, 20, 21)
├── Task 29: Comprehensive README + architecture docs [writing] (depends: all)
└── Task 30: .env.example + setup scripts [quick] (depends: 26)

Wave FINAL (Verification — After ALL tasks, 4 parallel):
├── Task F1: Plan compliance audit [oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real manual QA [unspecified-high] (+ playwright skill)
└── Task F4: Scope fidelity check [deep]

Critical Path: T1 → T2 → T8 → T14 → T15 → T17 → T20 → T21 → T26
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 7 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2-7 | 1 |
| 2 | 1 | 8, 9, 10, 12, 23 | 1 |
| 3 | 1 | 8, 9, 11 | 1 |
| 4 | 1 | 26 | 1 |
| 5 | 1 | 18, 19 | 1 |
| 6 | — | 16 | 1 |
| 7 | 1 | 13, 28 | 1 |
| 8 | 2, 3 | 14, 15 | 2 |
| 9 | 2, 3 | 14, 16, 23 | 2 |
| 10 | 2 | 14, 16 | 2 |
| 11 | 3 | 14, 16 | 2 |
| 12 | 2 | 21 | 2 |
| 13 | 7 | 21, 24 | 2 |
| 14 | 8, 9, 10, 11 | 15, 17 | 3 |
| 15 | 8, 14 | 17, 21 | 3 |
| 16 | 6, 9, 10, 11 | 25 | 3 |
| 17 | 14, 15 | 20 | 3 |
| 18 | 5 | 22 | 3 |
| 19 | 5 | 22 | 3 |
| 20 | 17 | 21, 28 | 4 |
| 21 | 12, 13, 15, 20 | 22, 26, 27 | 4 |
| 22 | 18, 19 | 26, 27 | 4 |
| 23 | 2, 9 | 24, 25 | 4 |
| 24 | 13, 23 | — | 4 |
| 25 | 16, 23 | 26 | 4 |
| 26 | 4, 21, 22, 25 | 30 | 5 |
| 27 | 21, 22 | — | 5 |
| 28 | 7, 20, 21 | — | 5 |
| 29 | all | — | 5 |
| 30 | 26 | — | 5 |

### Agent Dispatch Summary

| Wave | Tasks | Categories |
|------|-------|------------|
| 1 | 7 | T1→quick, T2→quick, T3→quick, T4→quick, T5→quick, T6→writing, T7→quick |
| 2 | 6 | T8→deep, T9→deep, T10→unspecified-high, T11→deep, T12→quick, T13→unspecified-high |
| 3 | 6 | T14→deep, T15→ultrabrain, T16→unspecified-high, T17→deep, T18→visual-engineering, T19→quick |
| 4 | 6 | T20→deep, T21→deep, T22→visual-engineering, T23→unspecified-high, T24→deep, T25→unspecified-high |
| 5 | 5 | T26→unspecified-high, T27→visual-engineering, T28→unspecified-high, T29→writing, T30→quick |
| FINAL | 4 | F1→oracle, F2→unspecified-high, F3→unspecified-high, F4→deep |

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**

### Wave 1 — Foundation (Start Immediately, 7 parallel)

- [x] 1. Monorepo Scaffolding + Configuration Files

  **What to do**:
  - Create monorepo directory structure:
    ```
    apps/
      backend/
        app/
          __init__.py
          main.py
          core/           # settings, logging, embeddings, docstore
          schemas/         # Pydantic models
          models/          # SQLAlchemy/DB models
          repositories/    # data access layer
          services/        # business logic
          agents/          # LangGraph agents
          routers/         # FastAPI endpoints
          middleware/      # auth, error handling
          workers/         # ARQ worker tasks
        tests/
          __init__.py
          core/
          schemas/
          repositories/
          services/
          agents/
          routers/
          workers/
          conftest.py      # shared fixtures
        pyproject.toml
        Dockerfile
        alembic.ini
        alembic/
      frontend/
        src/
          components/
          hooks/
          stores/
          types/
          lib/
          App.tsx
          main.tsx
        package.json
        tsconfig.json
        vite.config.ts
        vitest.config.ts
        Dockerfile
    data/                  # synthetic documents (generated in Task 6)
      it_support/
      legal/
      credit_card/
      airport_ground/
    scripts/
      ingest.py
      evaluate.py
    docker-compose.yml     # skeleton with all 8 services defined
    .env.example
    .gitignore
    ```
  - Create `pyproject.toml` with ALL pinned dependencies:
    - `fastapi`, `uvicorn[standard]`, `langchain-core`, `langchain-openai`, `langchain-community`, `langgraph`, `langgraph-supervisor`, `chromadb`, `redis`, `arq`, `pydantic-settings`, `structlog`, `tenacity`, `httpx`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `sentence-transformers`, `rank-bm25`
    - Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (test client), `ruff`
  - Create `package.json` with pinned dependencies:
    - `react`, `react-dom`, `zustand`, `@tanstack/react-query`
    - Dev: `typescript`, `vite`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@vitejs/plugin-react`, `tailwindcss`, `postcss`, `autoprefixer`
  - Create `.env.example` with all required environment variables documented
  - Create `.gitignore` for Python + Node + Docker

  **Must NOT do**:
  - Do NOT install `langchain` meta-package
  - Do NOT add Milvus dependencies
  - Do NOT use floating versions — pin ALL exact versions

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: File scaffolding with known patterns, no complex logic
  - **Skills**: []
    - No special skills needed for directory/config creation
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not a browser task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2-7)
  - **Blocks**: Tasks 2, 3, 4, 5, 7 (all Wave 1 tasks that need project structure)
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - [vstorm-co/full-stack-ai-agent-template](https://github.com/vstorm-co/full-stack-ai-agent-template) — Project structure reference: `API → Services → Repositories` layered architecture
  - [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) — LangGraph service project structure

  **External References**:
  - `langgraph-supervisor` PyPI page — confirm package name and latest version for pinning
  - `chromadb` PyPI page — latest stable version
  - Vite 6.x docs — project init config

  **WHY Each Reference Matters**:
  - vstorm template shows the exact layered architecture pattern (routers→services→repositories) that matches our interview decisions
  - agent-service-toolkit shows how to structure a LangGraph project specifically

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Project structure is correct and complete
    Tool: Bash
    Preconditions: Repository freshly cloned
    Steps:
      1. Run `ls apps/backend/app/` and verify directories: core, schemas, models, repositories, services, agents, routers, middleware, workers
      2. Run `ls apps/frontend/src/` and verify directories: components, hooks, stores, types, lib
      3. Run `ls data/` and verify directories: it_support, legal, credit_card, airport_ground
      4. Verify `cat apps/backend/pyproject.toml | grep "langchain-core"` returns a pinned version
      5. Verify `cat apps/backend/pyproject.toml | grep "langchain"` does NOT show bare `langchain` (only sub-packages)
      6. Verify `cat apps/frontend/package.json | grep "react"` returns a pinned version
    Expected Result: All directories exist, all deps pinned, no `langchain` meta-package
    Failure Indicators: Missing directory, floating version (^, ~, *), `langchain` without suffix in deps
    Evidence: .sisyphus/evidence/task-1-project-structure.txt

  Scenario: Dependencies install without errors
    Tool: Bash
    Preconditions: pyproject.toml and package.json created
    Steps:
      1. Run `cd apps/backend && pip install -e ".[dev]"` — expect exit code 0
      2. Run `cd apps/frontend && npm install` — expect exit code 0
    Expected Result: Both install commands succeed with exit 0
    Failure Indicators: Dependency resolution errors, version conflicts, missing packages
    Evidence: .sisyphus/evidence/task-1-deps-install.txt
  ```

  **Commit**: YES
  - Message: `feat: project scaffolding and monorepo structure`
  - Files: All scaffolding files
  - Pre-commit: `ls apps/backend/app/ && ls apps/frontend/src/`

- [x] 2. Backend Core Settings + Structured Logging

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/core/test_settings.py`:
    - Test `Settings` loads from environment variables
    - Test default values are sensible (EMBEDDING_PROVIDER=local, CHROMA_HOST=localhost, etc.)
    - Test validation (e.g., EMBEDDING_PROVIDER must be "local" or "azure")
  - **TDD: Write tests FIRST** in `tests/core/test_logging.py`:
    - Test `structlog` configuration produces JSON output
    - Test log includes timestamp, level, logger name
  - Implement `app/core/settings.py`:
    - Use `pydantic-settings.BaseSettings` with `.env` file support
    - Settings groups: Azure OpenAI (endpoint, key, deployment), Embedding (provider, model_name), ChromaDB (host, port), Redis (url, db numbers), PostgreSQL (dsn), API (key, host, port, debug), Logging (level, format)
  - Implement `app/core/logging.py`:
    - Configure `structlog` with JSON output, timestamper, log level filter
    - Create `get_logger(name)` factory function
  - Implement `app/core/__init__.py` with re-exports

  **Must NOT do**:
  - Do NOT hardcode any secrets or API keys
  - Do NOT use `logging.basicConfig` — use `structlog` only

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Pydantic settings pattern, well-documented
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3-7)
  - **Blocks**: Tasks 8, 9, 10, 12, 23
  - **Blocked By**: Task 1 (needs project structure)

  **References**:

  **Pattern References**:
  - `pydantic-settings` official docs — `BaseSettings` with `.env` file, nested settings groups
  - `structlog` official docs — JSON output, processor chain, `get_logger` pattern

  **External References**:
  - FastAPI settings docs: https://fastapi.tiangolo.com/advanced/settings/
  - structlog configuration: https://www.structlog.org/en/stable/configuration.html

  **WHY Each Reference Matters**:
  - Pydantic-settings provides type-safe config with env var loading — the standard pattern for FastAPI apps
  - structlog JSON output is critical for Docker log aggregation and debugging

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/core/test_settings.py`
  - [ ] Test file created: `tests/core/test_logging.py`
  - [ ] `pytest tests/core/test_settings.py tests/core/test_logging.py` → PASS

  **QA Scenarios:**

  ```
  Scenario: Settings load from environment variables
    Tool: Bash
    Preconditions: .env.example copied to .env with test values
    Steps:
      1. Run `cd apps/backend && EMBEDDING_PROVIDER=local python -c "from app.core.settings import get_settings; s = get_settings(); print(s.embedding_provider)"`
      2. Assert output is "local"
      3. Run `EMBEDDING_PROVIDER=azure python -c "from app.core.settings import get_settings; s = get_settings(); print(s.embedding_provider)"`
      4. Assert output is "azure"
    Expected Result: Settings correctly read from env vars
    Failure Indicators: ImportError, ValidationError, wrong value printed
    Evidence: .sisyphus/evidence/task-2-settings-env.txt

  Scenario: Invalid settings are rejected
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `EMBEDDING_PROVIDER=invalid python -c "from app.core.settings import get_settings; get_settings()"`
      2. Assert exit code is non-zero (ValidationError raised)
    Expected Result: Pydantic validation error for invalid embedding provider
    Failure Indicators: No error raised, or unrelated error
    Evidence: .sisyphus/evidence/task-2-settings-validation-error.txt

  Scenario: Structured logging produces JSON
    Tool: Bash
    Preconditions: Core logging module implemented
    Steps:
      1. Run `python -c "from app.core.logging import get_logger; log = get_logger('test'); log.info('hello', key='value')"`
      2. Assert output contains valid JSON with keys: "event", "timestamp", "level", "logger"
    Expected Result: JSON log line with all required fields
    Failure Indicators: Plain text output, missing fields, invalid JSON
    Evidence: .sisyphus/evidence/task-2-structured-logging.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): core settings, structured logging with TDD`
  - Files: `app/core/settings.py`, `app/core/logging.py`, `tests/core/test_settings.py`, `tests/core/test_logging.py`
  - Pre-commit: `pytest tests/core/`

- [x] 3. Pydantic Schemas + Type Definitions

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/schemas/test_schemas.py`:
    - Test ChatRequest serialization/validation (message: str, department: Optional[str], session_id: Optional[str])
    - Test ChatResponse structure (answer: str, department: str, sources: list, confidence: float, trace: AgentTrace)
    - Test AgentTrace structure (supervisor_decision: str, agents_invoked: list, retrieval_sources: list, iterations: int)
    - Test DocumentChunk, Department enum, EvaluationResult schemas
  - Implement `app/schemas/`:
    - `chat.py`: ChatRequest, ChatResponse, ChatStreamEvent, AgentTrace
    - `document.py`: DocumentChunk, DocumentMetadata, IngestionRequest, IngestionResult
    - `evaluation.py`: EvaluationRequest, EvaluationResult, RAGASMetrics
    - `common.py`: Department (enum: IT_SUPPORT, LEGAL, CREDIT_CARD, AIRPORT_GROUND), HealthResponse, ErrorResponse

  **Must NOT do**:
  - Do NOT create SQLAlchemy models here — those go in Task 7
  - Do NOT add business logic to schemas

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pydantic model definitions are straightforward, well-known patterns
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4-7)
  - **Blocks**: Tasks 8, 9, 11
  - **Blocked By**: Task 1 (needs project structure)

  **References**:

  **Pattern References**:
  - Pydantic v2 model docs — `BaseModel`, `Field`, validators, `model_config`

  **WHY Each Reference Matters**:
  - Schemas define the API contract — all downstream tasks (agents, services, routers) depend on these shapes

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/schemas/test_schemas.py`
  - [ ] `pytest tests/schemas/` → PASS

  **QA Scenarios:**

  ```
  Scenario: ChatRequest validates correctly
    Tool: Bash
    Preconditions: Schemas implemented
    Steps:
      1. Run `python -c "from app.schemas.chat import ChatRequest; r = ChatRequest(message='test'); print(r.model_dump_json())"`
      2. Assert output is valid JSON with "message" key
      3. Run `python -c "from app.schemas.chat import ChatRequest; ChatRequest()"` (missing required field)
      4. Assert exit code non-zero (ValidationError)
    Expected Result: Valid request serializes, invalid request raises ValidationError
    Failure Indicators: No validation error for missing field, wrong JSON shape
    Evidence: .sisyphus/evidence/task-3-schema-validation.txt

  Scenario: Department enum has all 4 values
    Tool: Bash
    Preconditions: Schemas implemented
    Steps:
      1. Run `python -c "from app.schemas.common import Department; print([d.value for d in Department])"`
      2. Assert output contains exactly: it_support, legal, credit_card, airport_ground
    Expected Result: 4 department values present
    Failure Indicators: Missing department, wrong naming
    Evidence: .sisyphus/evidence/task-3-department-enum.txt
  ```

  **Commit**: YES (groups with Task 2)
  - Message: `feat(backend): Pydantic schemas and type definitions with TDD`
  - Files: `app/schemas/*.py`, `tests/schemas/test_schemas.py`
  - Pre-commit: `pytest tests/schemas/`

- [x] 4. Docker Compose Skeleton + Service Configs

  **What to do**:
  - Create `docker-compose.yml` with all 8 services defined (but API/Worker/Frontend as stubs):
    - `api`: FastAPI app (Dockerfile in apps/backend/, port 8000)
    - `worker`: ARQ worker (same image as api, different entrypoint)
    - `redis`: Redis 7.x (port 6379, two DBs: db0=cache, db1=arq)
    - `chromadb`: ChromaDB server (port 8001, volume mount `/chroma/data`)
    - `postgres`: PostgreSQL 16 (port 5432, volume mount, init SQL for database creation)
    - `nginx`: Nginx reverse proxy (port 80→8000/3000, SSE config)
    - `frontend`: Vite dev server (port 3000)
    - `seed`: One-shot container for initial data seeding (depends_on: chromadb, postgres)
  - Create `apps/backend/Dockerfile` (Python 3.12 slim, multi-stage build, pre-download bge-base-en-v1.5 model)
  - Create `apps/frontend/Dockerfile` (Node 20, multi-stage build)
  - Create `nginx/nginx.conf` with:
    - `proxy_buffering off` for SSE
    - `proxy_read_timeout 300s` for long agent responses
    - `X-Accel-Buffering: no` header
    - Route `/api/` → api:8000, `/` → frontend:3000
  - Add health checks for all services
  - Create `docker-compose.dev.yml` override for development (volume mounts, hot reload)

  **Must NOT do**:
  - Do NOT add Kubernetes, Terraform, or CI/CD configs
  - Do NOT add Milvus service
  - Do NOT expose PostgreSQL/Redis ports in production (only via internal Docker network)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Docker Compose configuration with known service patterns
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-3, 5-7)
  - **Blocks**: Task 26 (production Docker config)
  - **Blocked By**: Task 1 (needs project structure)

  **References**:

  **Pattern References**:
  - ChromaDB Docker docs — `chromadb/chroma:latest` image, persistence volume, `HttpClient` configuration
  - Official Nginx SSE proxy docs — `proxy_buffering off`, `proxy_read_timeout`

  **External References**:
  - ChromaDB Docker setup: https://docs.trychroma.com/deployment/docker
  - Nginx SSE proxy: https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering

  **WHY Each Reference Matters**:
  - ChromaDB Docker config is essential for multi-container setup where API and worker connect via `HttpClient`
  - Nginx SSE config is a known gotcha — without `proxy_buffering off`, streams get buffered and appear non-streaming

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Docker Compose validates without errors
    Tool: Bash
    Preconditions: docker-compose.yml created
    Steps:
      1. Run `docker compose config --quiet` in project root
      2. Assert exit code 0
      3. Run `docker compose config --services` and verify 8 services listed
    Expected Result: Valid compose file with 8 services
    Failure Indicators: YAML parsing error, missing service definitions, wrong port mappings
    Evidence: .sisyphus/evidence/task-4-docker-compose-config.txt

  Scenario: Nginx config has SSE-critical directives
    Tool: Bash
    Preconditions: nginx.conf created
    Steps:
      1. Run `grep "proxy_buffering off" nginx/nginx.conf`
      2. Run `grep "proxy_read_timeout 300s" nginx/nginx.conf`
      3. Run `grep "X-Accel-Buffering" nginx/nginx.conf`
    Expected Result: All 3 SSE-critical directives present
    Failure Indicators: Missing directive (SSE will buffer/timeout in production)
    Evidence: .sisyphus/evidence/task-4-nginx-sse-config.txt

  Scenario: Backend Dockerfile pre-downloads embedding model
    Tool: Bash
    Preconditions: Dockerfile created
    Steps:
      1. Run `grep "bge-base-en-v1.5" apps/backend/Dockerfile`
      2. Assert the RUN instruction downloads the model during build
    Expected Result: Model download instruction present in Dockerfile
    Failure Indicators: Missing pre-download (first run would fail without internet)
    Evidence: .sisyphus/evidence/task-4-dockerfile-embedding-preload.txt
  ```

  **Commit**: YES
  - Message: `feat(docker): Docker Compose skeleton with all services, Nginx SSE config`
  - Files: `docker-compose.yml`, `docker-compose.dev.yml`, `apps/backend/Dockerfile`, `apps/frontend/Dockerfile`, `nginx/nginx.conf`
  - Pre-commit: `docker compose config --quiet`

- [x] 5. Frontend Scaffolding (Vite + React + shadcn/ui + Zustand)

  **What to do**:
  - Initialize Vite + React + TypeScript project in `apps/frontend/`
  - Configure Tailwind CSS v4 + shadcn/ui
  - Configure Vitest with React Testing Library
  - Set up base layout with:
    - `src/App.tsx` — root layout with sidebar/header placeholder
    - `src/main.tsx` — React root with providers
    - `src/lib/utils.ts` — shadcn/ui `cn()` utility
  - Set up Zustand store skeleton:
    - `src/stores/chatStore.ts` — chat state (messages, loading, department, sessionId) with `devtools` middleware
  - Set up TypeScript types:
    - `src/types/chat.ts` — ChatMessage, ChatRequest, ChatResponse, AgentTrace, Department
    - `src/types/api.ts` — SSEEvent, APIError
  - Write initial Vitest test:
    - `src/stores/__tests__/chatStore.test.ts` — test initial state, addMessage action

  **Must NOT do**:
  - Do NOT add routing library (single-page app, no navigation needed)
  - Do NOT add Playwright/Cypress
  - Do NOT build actual chat components yet (Task 18)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Vite + React scaffolding with known tools
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: Save for Task 18 (actual UI building)
    - `playwright`: No E2E tests

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-4, 6-7)
  - **Blocks**: Tasks 18, 19
  - **Blocked By**: Task 1 (needs project structure)

  **References**:

  **External References**:
  - Vite React TypeScript template: `npm create vite@latest -- --template react-ts`
  - shadcn/ui installation: https://ui.shadcn.com/docs/installation/vite
  - Zustand devtools middleware: https://docs.pmnd.rs/zustand/middlewares/devtools

  **WHY Each Reference Matters**:
  - Vite template ensures correct TypeScript config and HMR setup
  - shadcn/ui requires specific Tailwind + alias configuration
  - Zustand devtools enables Redux DevTools integration for debugging

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `src/stores/__tests__/chatStore.test.ts`
  - [ ] `npx vitest run` → PASS

  **QA Scenarios:**

  ```
  Scenario: Frontend dev server starts without errors
    Tool: Bash
    Preconditions: npm install completed
    Steps:
      1. Run `cd apps/frontend && npx vite build` (production build test)
      2. Assert exit code 0
      3. Run `ls apps/frontend/dist/index.html`
      4. Assert file exists
    Expected Result: Vite builds successfully, dist/index.html produced
    Failure Indicators: TypeScript errors, missing dependencies, build failure
    Evidence: .sisyphus/evidence/task-5-frontend-build.txt

  Scenario: Vitest runs and passes initial test
    Tool: Bash
    Preconditions: Vitest configured, initial test written
    Steps:
      1. Run `cd apps/frontend && npx vitest run --reporter=verbose`
      2. Assert output shows "chatStore" test suite with passing tests
      3. Assert exit code 0
    Expected Result: At least 1 test passes, 0 failures
    Failure Indicators: Test configuration error, import errors, failing tests
    Evidence: .sisyphus/evidence/task-5-vitest-initial.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): React + TypeScript scaffolding with shadcn/ui, Zustand, Vitest`
  - Files: `apps/frontend/src/**`, `apps/frontend/package.json`, `apps/frontend/vite.config.ts`, `apps/frontend/vitest.config.ts`
  - Pre-commit: `cd apps/frontend && npx vitest run`

- [x] 6. Synthetic Airline Documents for 4 Departments

  **What to do**:
  - Generate realistic but synthetic airline knowledge base documents in Markdown format
  - **IT Support** (`data/it_support/`): 8-10 documents
    - VPN setup and troubleshooting guide
    - Password reset procedures (SSO, email, VPN)
    - Software installation request process
    - Laptop provisioning and return policy
    - WiFi connectivity guide (office + airport lounges)
    - Email configuration (Outlook, mobile devices)
    - IT security policies (2FA, phishing awareness)
    - Help desk escalation procedures
  - **Legal** (`data/legal/`): 8-10 documents
    - Passenger rights and compensation policies (EU261, DOT regulations)
    - Data privacy policy (GDPR compliance for passenger data)
    - Terms and conditions of carriage
    - Baggage liability and claims procedures
    - Employee code of conduct
    - Intellectual property and confidentiality agreements
    - Regulatory compliance overview (FAA, EASA)
    - Contract templates for vendor agreements
  - **Credit Card** (`data/credit_card/`): 8-10 documents
    - Co-branded credit card program overview
    - Miles earning and redemption rates
    - Credit card tier benefits (Silver, Gold, Platinum)
    - Annual fee waiver conditions
    - Fraud detection and dispute resolution
    - Partner merchant bonus categories
    - Statement credit and cashback policies
    - Card application and approval criteria
  - **Airport Ground Services** (`data/airport_ground/`): 8-10 documents
    - Check-in procedures (online, kiosk, counter)
    - Baggage weight limits and excess fees (domestic/international)
    - Special handling (wheelchairs, pets, unaccompanied minors)
    - Lounge access policies and amenities
    - Flight delay and cancellation handling procedures
    - Gate assignment and boarding procedures
    - Lost and found procedures
    - Ground transportation partnerships
  - Each document should be 500-1500 words with clear headings, realistic detail
  - Include metadata headers (department, last_updated, category, audience)

  **Must NOT do**:
  - Do NOT copy real airline content — generate original synthetic content
  - Do NOT create overly generic content — include specific fictional policies with numbers/thresholds
  - Do NOT create PDFs or complex formats — Markdown only

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Content generation task — creating realistic technical documents
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-5, 7)
  - **Blocks**: Task 16 (document ingestion)
  - **Blocked By**: None (can start immediately — just creates .md files)

  **References**:

  **External References**:
  - EU261 passenger rights regulations — for realistic legal department content
  - IATA baggage rules — for realistic ground services content

  **WHY Each Reference Matters**:
  - Real airline regulation names and policy patterns make synthetic documents believable for demos

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: All departments have sufficient documents
    Tool: Bash
    Preconditions: Documents generated
    Steps:
      1. Run `ls data/it_support/*.md | wc -l` — assert >= 8
      2. Run `ls data/legal/*.md | wc -l` — assert >= 8
      3. Run `ls data/credit_card/*.md | wc -l` — assert >= 8
      4. Run `ls data/airport_ground/*.md | wc -l` — assert >= 8
      5. Run `wc -w data/it_support/*.md` — assert total > 4000 words
    Expected Result: At least 8 documents per department, each 500+ words
    Failure Indicators: Missing files, empty files, too short content
    Evidence: .sisyphus/evidence/task-6-doc-counts.txt

  Scenario: Documents have proper metadata headers
    Tool: Bash
    Preconditions: Documents generated
    Steps:
      1. Run `head -10 data/it_support/vpn-setup.md`
      2. Assert output contains metadata fields: department, last_updated, category
      3. Repeat for one document in each other department
    Expected Result: All documents have consistent metadata headers
    Failure Indicators: Missing metadata, inconsistent format
    Evidence: .sisyphus/evidence/task-6-doc-metadata.txt
  ```

  **Commit**: YES
  - Message: `content: synthetic airline knowledge base documents for 4 departments`
  - Files: `data/**/*.md`
  - Pre-commit: `ls data/it_support/*.md data/legal/*.md data/credit_card/*.md data/airport_ground/*.md | wc -l`

- [x] 7. PostgreSQL Models + Alembic Migrations

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/models/test_models.py`:
    - Test `Conversation` model creation and serialization
    - Test `Message` model with conversation FK relationship
    - Test `EvaluationResult` model
  - Implement SQLAlchemy async models in `app/models/`:
    - `base.py`: Base declarative model, async engine factory, async session factory
    - `conversation.py`: `Conversation` (id, session_id, department, created_at, updated_at)
    - `message.py`: `Message` (id, conversation_id FK, role: user|assistant|system, content, sources JSON, trace JSON, created_at)
    - `evaluation.py`: `EvaluationResult` (id, conversation_id FK, faithfulness, answer_relevancy, context_precision, context_recall, created_at)
  - Configure Alembic for async migrations:
    - `alembic.ini` with `sqlalchemy.url` from settings
    - `alembic/env.py` with async engine support
    - Initial migration: create all tables
  - Create `app/core/database.py`: async engine, session factory, `get_db_session` dependency

  **Must NOT do**:
  - Do NOT implement CRUD operations here (that's Task 13)
  - Do NOT add user/auth models (no JWT auth)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard SQLAlchemy model definitions with Alembic setup
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1-6)
  - **Blocks**: Tasks 13, 28
  - **Blocked By**: Task 1 (needs project structure)

  **References**:

  **External References**:
  - SQLAlchemy 2.0 async docs: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
  - Alembic async tutorial: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic

  **WHY Each Reference Matters**:
  - SQLAlchemy 2.0 async API differs significantly from 1.x — must use correct `create_async_engine` and `AsyncSession`
  - Alembic async configuration has specific `env.py` patterns that differ from sync

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file created: `tests/models/test_models.py`
  - [ ] `pytest tests/models/` → PASS

  **QA Scenarios:**

  ```
  Scenario: Alembic migration generates correct tables
    Tool: Bash
    Preconditions: PostgreSQL running (can use SQLite for test), models defined
    Steps:
      1. Run `cd apps/backend && alembic upgrade head`
      2. Assert exit code 0
      3. Run `alembic current` and assert it shows head revision
    Expected Result: Migration applies cleanly, all tables created
    Failure Indicators: Migration error, SQL syntax error, missing table
    Evidence: .sisyphus/evidence/task-7-alembic-migration.txt

  Scenario: Model relationships work correctly
    Tool: Bash
    Preconditions: Models and migration applied
    Steps:
      1. Run Python script that creates Conversation → adds Message → queries back
      2. Assert Message.conversation relationship resolves correctly
      3. Assert Conversation.messages back-reference returns the message
    Expected Result: FK relationships work bidirectionally
    Failure Indicators: Integrity error, missing relationship, wrong cascade
    Evidence: .sisyphus/evidence/task-7-model-relationships.txt
  ```

  **Commit**: YES (groups with Task 2)
  - Message: `feat(backend): PostgreSQL models and Alembic async migrations`
  - Files: `app/models/*.py`, `app/core/database.py`, `alembic/`, `tests/models/test_models.py`
  - Pre-commit: `pytest tests/models/`

### Wave 2 — Core RAG Pipeline (After Wave 1, 6 parallel)

- [x] 8. Dual Embedding Factory (bge-base-en-v1.5 / Azure OpenAI)
- [x] 9. ChromaDB Repository + Batch Operations
- [x] 10. Redis-Backed Docstore for Parent Documents
- [x] 11. Document Chunking Pipeline (Parent-Child + RecursiveCharacter)
- [x] 12. API Key Auth Middleware + Health Endpoints
- [x] 13. Conversation Repository (PostgreSQL CRUD)

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/repositories/test_conversation.py`:
    - Test `create_conversation(session_id, department)` inserts row, returns Conversation
    - Test `get_conversation(session_id)` retrieves existing conversation
    - Test `add_message(conversation_id, role, content, sources, trace)` inserts Message
    - Test `get_messages(conversation_id, limit, offset)` returns ordered messages
    - Test `get_or_create_conversation(session_id)` creates if not exists, returns if exists
    - Use `pytest-asyncio` with in-memory SQLite for tests
  - Implement `app/repositories/conversation.py`:
    - `ConversationRepository` class using async SQLAlchemy sessions
    - CRUD methods for Conversation and Message models
    - `get_messages_for_context(conversation_id, limit=10)` — returns recent messages formatted for LangChain message history
    - `save_agent_response(conversation_id, response, trace)` — saves assistant message with sources and agent trace

  **Must NOT do**:
  - Do NOT implement caching — direct PostgreSQL queries are fast enough
  - Do NOT add pagination API — just `limit/offset` at repository level

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Async SQLAlchemy patterns with proper session management
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 8-12)
  - **Blocks**: Tasks 21, 24
  - **Blocked By**: Task 7 (PostgreSQL models)

  **References**:

  **Pattern References**:
  - SQLAlchemy 2.0 async session docs — `async with AsyncSession(engine) as session` pattern
  - FastAPI dependency injection for async DB sessions

  **WHY Each Reference Matters**:
  - Async session management must be correct to avoid connection pool exhaustion under load

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/repositories/test_conversation.py`
  - [ ] `pytest tests/repositories/test_conversation.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Full conversation lifecycle
    Tool: Bash
    Preconditions: Models migrated (SQLite for test)
    Steps:
      1. Create conversation with session_id="test-session-1", department="it_support"
      2. Add user message "How do I reset my VPN?"
      3. Add assistant message with sources and trace
      4. Retrieve messages for conversation — assert 2 messages in order
      5. Call `get_or_create_conversation("test-session-1")` — assert returns same conversation (no duplicate)
    Expected Result: Full CRUD cycle works, no duplicates on get_or_create
    Failure Indicators: Duplicate conversations, wrong message order, missing sources/trace
    Evidence: .sisyphus/evidence/task-13-conversation-lifecycle.txt

  Scenario: Message context retrieval for agent history
    Tool: Bash
    Preconditions: Conversation with 15 messages
    Steps:
      1. Add 15 messages to a conversation
      2. Call `get_messages_for_context(conversation_id, limit=10)`
      3. Assert exactly 10 most recent messages returned
      4. Assert messages are in chronological order
    Expected Result: Last 10 messages returned in order
    Failure Indicators: Wrong count, wrong order, all 15 returned
    Evidence: .sisyphus/evidence/task-13-context-retrieval.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): conversation repository with PostgreSQL async CRUD`
  - Files: `app/repositories/conversation.py`, `tests/repositories/test_conversation.py`
  - Pre-commit: `pytest tests/repositories/test_conversation.py`

### Wave 3 — Agents + Retrieval (After Wave 2, 6 parallel)

- [x] 14. Hybrid Retriever (BM25 + Vector EnsembleRetriever)

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/services/test_retrieval.py`:
    - Test `HybridRetriever.retrieve(query, department, k)` returns ranked documents
    - Test BM25 and Vector results are merged via RRF (Reciprocal Rank Fusion)
    - Test per-department isolation (IT query doesn't return Legal docs)
    - Test fallback: if BM25 is empty (no docs loaded yet), falls back to vector-only
    - Test `k` parameter limits results correctly
    - Mock ChromaDB with in-memory client, mock BM25 with small doc set
  - Implement `app/services/retrieval.py`:
    - `HybridRetriever` class
    - Initialize per-department: `BM25Retriever` (from `rank_bm25`) + Chroma vector retriever
    - Use `EnsembleRetriever` from `langchain_community.retrievers` (or `langchain.retrievers.ensemble`) with RRF
    - Weights: `[0.4, 0.6]` (40% BM25, 60% vector) — tunable via settings
    - Lazy initialization: BM25 indexes built on first query per department (not on startup)
    - `retrieve(query: str, department: Department, k: int = 5) -> list[Document]`
    - Return child chunks from vector search, then fetch parent chunks from RedisDocStore for context

  **Must NOT do**:
  - Do NOT add Elasticsearch for BM25 — use in-memory `rank-bm25` library
  - Do NOT load all departments' docs into memory at startup — lazy per-department

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex retrieval logic combining BM25 + Vector with RRF, parent-child resolution
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 15-19)
  - **Blocks**: Tasks 15, 17
  - **Blocked By**: Tasks 8 (embeddings), 9 (ChromaDB), 10 (Redis docstore), 11 (chunking)

  **References**:

  **External References**:
  - LangChain `EnsembleRetriever` docs — `retrievers` list, `weights` list, RRF fusion
  - `rank-bm25` PyPI — BM25Okapi implementation
  - Research finding: hybrid search improves recall 12-18% over vector-only

  **WHY Each Reference Matters**:
  - `EnsembleRetriever` handles RRF fusion automatically — no need to implement RRF manually
  - `rank-bm25` is the standard Python BM25 implementation, lightweight and dependency-free

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/services/test_retrieval.py`
  - [ ] `pytest tests/services/test_retrieval.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Hybrid search returns relevant results from correct department
    Tool: Bash
    Preconditions: ChromaDB loaded with IT Support docs, BM25 initialized
    Steps:
      1. Ingest 5 IT Support documents and 5 Legal documents into separate collections
      2. Query `retrieve("VPN password reset", department=Department.IT_SUPPORT, k=3)`
      3. Assert all 3 results have department="it_support" in metadata
      4. Assert results contain content related to VPN
    Expected Result: 3 IT Support results about VPN, no Legal docs leaked
    Failure Indicators: Cross-department contamination, irrelevant results, empty results
    Evidence: .sisyphus/evidence/task-14-hybrid-retrieval.txt

  Scenario: Parent document resolution from child chunks
    Tool: Bash
    Preconditions: Parent-child chunks ingested
    Steps:
      1. Query returns child chunks
      2. Verify each child chunk's parent_id resolves to a parent document in RedisDocStore
      3. Verify parent content is larger than child content
    Expected Result: Child→parent resolution works correctly
    Failure Indicators: Missing parent document, parent_id mismatch
    Evidence: .sisyphus/evidence/task-14-parent-resolution.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): hybrid retriever (BM25 + Vector) with EnsembleRetriever and TDD`
  - Files: `app/services/retrieval.py`, `tests/services/test_retrieval.py`
  - Pre-commit: `pytest tests/services/test_retrieval.py`

- [x] 15. Self-RAG StateGraph with Critique Loop

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/agents/test_self_rag.py`:
    - Test graph executes: retrieve → generate → critique → (refine or return)
    - Test critique approves good answer → returns immediately (1 iteration)
    - Test critique rejects bad answer → triggers rewrite + re-retrieve (up to 3 iterations)
    - Test hard cap at 3 iterations via `RemainingSteps`
    - Test unanswerable query → returns "I don't have information" style response
    - Mock LLM with `FakeListChatModel` — no real API calls
  - Implement `app/agents/self_rag.py`:
    - `SelfRAGState(TypedDict)`: query, documents, generation, critique_result, iteration_count, remaining_steps
    - StateGraph nodes:
      - `retrieve`: calls HybridRetriever for relevant documents
      - `generate`: LLM generates answer from documents
      - `critique`: LLM evaluates answer quality (faithfulness, relevance, completeness)
      - `rewrite_query`: LLM rewrites query for better retrieval
    - Conditional edges:
      - After `critique`: if approved → END, if rejected AND remaining_steps > 7 → `rewrite_query` → `retrieve`
      - If remaining_steps <= 7 → END with best-effort answer + low confidence flag
    - Use `RemainingSteps` from `langgraph.types` for iteration control
    - Set `recursion_limit=10` in graph config (3 full cycles × 3 nodes + 1 buffer)
    - Include confidence score in output (0.0-1.0 based on critique assessment)
    - Use `tenacity` retry with exponential backoff on LLM calls

  **Must NOT do**:
  - Do NOT use Python for-loops for iteration — use LangGraph conditional edges
  - Do NOT set recursion_limit > 15 (unnecessary, wastes tokens)
  - Do NOT skip the critique step — it's the "agentic" part of Agentic RAG

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: Complex StateGraph with conditional routing, iteration control, and LLM-as-judge pattern — the most technically challenging component
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14, 16-19)
  - **Blocks**: Tasks 17, 21
  - **Blocked By**: Tasks 8 (embeddings), 14 (hybrid retriever)

  **References**:

  **Pattern References**:
  - jamwithai/production-agentic-rag-course — graph structure: guardrail → retrieve → grade_documents → rewrite → generate
  - LangGraph `RemainingSteps` docs — managed value for iteration control in cyclic graphs

  **External References**:
  - LangGraph StateGraph tutorial: https://langchain-ai.github.io/langgraph/concepts/low_level/
  - LangGraph conditional edges: `add_conditional_edges(source, condition_fn, path_map)`
  - Self-RAG paper pattern: retrieve → generate → critique → (refine or accept)
  - `langchain_core.language_models.fake_chat_models.FakeListChatModel` for testing

  **WHY Each Reference Matters**:
  - jamwithai's flow is the closest production reference to our Self-RAG pattern — shows exact node/edge structure
  - `RemainingSteps` is the LangGraph-native way to control iteration — avoids manual counter anti-pattern
  - `FakeListChatModel` enables deterministic testing without API calls

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/agents/test_self_rag.py`
  - [ ] `pytest tests/agents/test_self_rag.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Good answer approved in 1 iteration
    Tool: Bash
    Preconditions: Self-RAG graph compiled, FakeListChatModel configured to approve
    Steps:
      1. Invoke graph with query="What is the baggage weight limit?" and relevant docs
      2. Assert graph exits after 1 critique (no rewrite loop)
      3. Assert output has confidence > 0.7
      4. Assert output contains answer text
    Expected Result: Single-pass approval with high confidence
    Failure Indicators: Multiple iterations for good answer, missing confidence score
    Evidence: .sisyphus/evidence/task-15-self-rag-approve.txt

  Scenario: Bad answer triggers retry up to 3 iterations then returns best-effort
    Tool: Bash
    Preconditions: FakeListChatModel configured to always reject
    Steps:
      1. Invoke graph with query and poor-quality docs
      2. Assert graph loops exactly 3 times (critique → rewrite → retrieve × 3)
      3. Assert graph terminates (doesn't infinite loop)
      4. Assert output has confidence < 0.5
    Expected Result: Exactly 3 iterations, graceful termination, low confidence
    Failure Indicators: Infinite loop, >3 iterations, crash, no confidence score
    Evidence: .sisyphus/evidence/task-15-self-rag-retry-cap.txt

  Scenario: Unanswerable query returns appropriate response
    Tool: Bash
    Preconditions: Graph compiled, empty document set
    Steps:
      1. Invoke graph with query="What is the CEO's salary?" and no relevant docs
      2. Assert output answer contains phrasing like "don't have" or "not available" or "cannot find"
      3. Assert confidence is very low (< 0.3)
    Expected Result: Graceful "I don't know" response, not hallucination
    Failure Indicators: Hallucinated answer, confidence > 0.5 with no docs
    Evidence: .sisyphus/evidence/task-15-self-rag-unanswerable.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): Self-RAG StateGraph with critique loop and iteration control`
  - Files: `app/agents/self_rag.py`, `tests/agents/test_self_rag.py`
  - Pre-commit: `pytest tests/agents/test_self_rag.py`

- [x] 16. Document Ingestion Service + CLI Script

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/services/test_ingestion.py`:
    - Test `IngestionService.ingest_department(department, data_dir)` processes all .md files
    - Test ingestion creates child chunks in ChromaDB and parent chunks in Redis docstore
    - Test ingestion is idempotent (re-running doesn't duplicate documents)
    - Test metadata is correctly set (department, source_file, chunk_type)
  - Implement `app/services/ingestion.py`:
    - `IngestionService` class orchestrating: file loading → chunking → embedding → storage
    - Load Markdown files from `data/{department}/` directory
    - Use `ChunkingService` (Task 11) to create parent-child chunks
    - Store child chunks in ChromaDB via `ChromaRepository` (Task 9)
    - Store parent chunks in `RedisDocStore` (Task 10)
    - Embed child chunks using `get_embedding_model` (Task 8)
    - Track ingested files to prevent duplication (store hash in Redis)
  - Implement `scripts/ingest.py`:
    - CLI script: `python scripts/ingest.py --department it_support` or `--all`
    - Progress logging with structlog
    - Reports: documents processed, chunks created, time elapsed

  **Must NOT do**:
  - Do NOT add PDF/DOCX processing — Markdown only
  - Do NOT allow concurrent ingestion to same collection — sequential per department
  - Do NOT add a document upload UI

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integration service connecting multiple components (chunking, ChromaDB, Redis, embeddings)
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14, 15, 17-19)
  - **Blocks**: Task 25 (seed data ingestion)
  - **Blocked By**: Tasks 6 (synthetic docs), 9 (ChromaDB), 10 (Redis docstore), 11 (chunking)

  **References**:

  **Pattern References**:
  - Tasks 9, 10, 11 — this task orchestrates all three into a cohesive pipeline

  **WHY Each Reference Matters**:
  - This is the integration layer — must correctly wire ChromaRepository + RedisDocStore + ChunkingService

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/services/test_ingestion.py`
  - [ ] `pytest tests/services/test_ingestion.py` → PASS (4+ tests)

  **QA Scenarios:**

  ```
  Scenario: Ingest IT Support department documents
    Tool: Bash
    Preconditions: Synthetic docs in data/it_support/, ChromaDB and Redis running
    Steps:
      1. Run `python scripts/ingest.py --department it_support`
      2. Assert exit code 0
      3. Verify ChromaDB collection `it_support_knowledge_base` exists and has documents
      4. Query ChromaDB for "VPN" — assert results returned
      5. Verify Redis has parent documents (keys matching `docstore:it_support:*`)
    Expected Result: Documents ingested, searchable in ChromaDB, parents in Redis
    Failure Indicators: Empty collection, missing Redis keys, ingestion error
    Evidence: .sisyphus/evidence/task-16-ingest-it-support.txt

  Scenario: Re-ingestion is idempotent
    Tool: Bash
    Preconditions: IT Support already ingested
    Steps:
      1. Count documents in `it_support_knowledge_base` — record count N
      2. Run `python scripts/ingest.py --department it_support` again
      3. Count documents again — assert still N (no duplicates)
    Expected Result: Same document count after re-ingestion
    Failure Indicators: Document count doubled
    Evidence: .sisyphus/evidence/task-16-idempotent-ingest.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): document ingestion service and CLI script with TDD`
  - Files: `app/services/ingestion.py`, `scripts/ingest.py`, `tests/services/test_ingestion.py`
  - Pre-commit: `pytest tests/services/test_ingestion.py`

- [x] 17. Department Agent Factory (create_react_agent × 4)

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/agents/test_department_agents.py`:
    - Test `create_department_agent(department, llm, tools)` returns a compiled graph
    - Test each agent has a `rag_search` tool bound to its department
    - Test agent invocation with mock LLM produces structured output
    - Test agent timeout (30s) via `asyncio.wait_for`
    - Test 4 agents can be created with different department configs
  - Implement `app/agents/department.py`:
    - `DepartmentAgentFactory` class
    - For each department, create:
      - RAG tool: `rag_search(query: str) -> str` that calls HybridRetriever + Self-RAG for that department
      - System prompt: department-specific instructions (e.g., "You are an IT Support specialist for SkyWing Airlines...")
      - Agent: `create_react_agent(model=llm, tools=[rag_search], name=f"{dept}_agent", prompt=system_prompt)`
    - `create_all_agents(llm, retrieval_service) -> dict[Department, CompiledGraph]`
    - Per-agent timeout wrapper: `asyncio.wait_for(agent.ainvoke(...), timeout=30)`
    - Use `tenacity` retry on LLM calls within tools

  **Must NOT do**:
  - Do NOT create custom agent classes — use `create_react_agent` from `langgraph.prebuilt`
  - Do NOT allow agents to access other departments' knowledge bases
  - Do NOT skip the system prompt — each agent MUST have department-specific instructions

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: LangGraph agent creation with tool binding and department isolation
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14-16, 18-19)
  - **Blocks**: Task 20 (Supervisor)
  - **Blocked By**: Tasks 14 (hybrid retriever), 15 (Self-RAG)

  **References**:

  **Pattern References**:
  - `langgraph.prebuilt.create_react_agent` docs — `model`, `tools`, `name`, `prompt` parameters
  - langgraph-supervisor-py README — shows `create_react_agent` usage with `create_supervisor`

  **External References**:
  - LangGraph create_react_agent: https://langchain-ai.github.io/langgraph/reference/prebuilt/#create_react_agent
  - Agent tool binding pattern: tools receive department context via closure

  **WHY Each Reference Matters**:
  - `create_react_agent` is the official LangGraph prebuilt agent — ensures compatibility with `create_supervisor`
  - Department isolation is achieved via tool closures, not agent configuration

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/agents/test_department_agents.py`
  - [ ] `pytest tests/agents/test_department_agents.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Department agent answers domain-specific query
    Tool: Bash
    Preconditions: IT Support agent created with mock LLM and retriever
    Steps:
      1. Create IT Support agent via factory
      2. Invoke with "How do I reset my VPN password?"
      3. Assert agent uses `rag_search` tool (check tool calls in trace)
      4. Assert response contains VPN-related content
    Expected Result: Agent calls RAG tool and produces relevant answer
    Failure Indicators: Agent doesn't use tool, irrelevant response, timeout
    Evidence: .sisyphus/evidence/task-17-dept-agent-query.txt

  Scenario: Agent respects 30-second timeout
    Tool: Bash
    Preconditions: Agent with slow mock LLM (simulated delay)
    Steps:
      1. Create agent with LLM that takes 60 seconds to respond
      2. Invoke with timeout wrapper
      3. Assert `asyncio.TimeoutError` is raised within ~30 seconds
    Expected Result: Timeout raised at 30s, not waiting 60s
    Failure Indicators: Waits full 60s, no timeout error
    Evidence: .sisyphus/evidence/task-17-agent-timeout.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): 4 department agents with create_react_agent and TDD`
  - Files: `app/agents/department.py`, `tests/agents/test_department_agents.py`
  - Pre-commit: `pytest tests/agents/test_department_agents.py`

- [x] 18. Frontend Chat UI Components

  **What to do**:
  - **TDD: Write component tests FIRST** in `src/components/__tests__/`:
    - Test `ChatMessage` renders user and assistant messages differently
    - Test `ChatInput` calls onSend callback with message text
    - Test `DepartmentSelector` renders 4 departments and calls onChange
    - Test `SourceCard` renders citation with title and snippet
  - Implement `src/components/`:
    - `ChatMessage.tsx`: renders single message (user vs assistant styling, markdown support)
    - `ChatInput.tsx`: text input + send button, disabled when loading
    - `ChatMessageList.tsx`: scrollable message list with auto-scroll-to-bottom
    - `DepartmentSelector.tsx`: dropdown with 4 departments + "Auto" option (Supervisor decides)
    - `SourceCard.tsx`: displays a single retrieval source (title, snippet, department badge)
    - `SourceList.tsx`: grid/list of SourceCards from response
    - `LoadingIndicator.tsx`: pulsing dots or spinner for streaming state
  - Use shadcn/ui components: `Button`, `Input`, `Select`, `Card`, `Badge`, `ScrollArea`
  - All components are presentational (no API calls — that's Task 19/22)

  **Must NOT do**:
  - Do NOT add API calling logic — components receive data via props
  - Do NOT add routing — single page
  - Do NOT use Playwright for testing — Vitest + React Testing Library only

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI component development with design system (shadcn/ui)
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Crafts UI components with proper styling, accessibility, and UX patterns
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not used for component tests

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14-17, 19)
  - **Blocks**: Task 22 (page assembly)
  - **Blocked By**: Task 5 (frontend scaffolding)

  **References**:

  **External References**:
  - shadcn/ui component library: https://ui.shadcn.com/docs/components
  - React Testing Library docs: https://testing-library.com/docs/react-testing-library/intro

  **WHY Each Reference Matters**:
  - shadcn/ui provides the base components — must use their API correctly (not re-implement)
  - React Testing Library enforces testing user behavior, not implementation details

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test files in `src/components/__tests__/`
  - [ ] `npx vitest run` → PASS (all component tests)

  **QA Scenarios:**

  ```
  Scenario: Chat components render correctly
    Tool: Bash
    Preconditions: Components implemented
    Steps:
      1. Run `cd apps/frontend && npx vitest run --reporter=verbose`
      2. Assert ChatMessage test: user message has different class than assistant message
      3. Assert ChatInput test: onSend called with correct text
      4. Assert DepartmentSelector test: 4 departments + Auto rendered
      5. Assert all tests pass
    Expected Result: All component tests pass
    Failure Indicators: Render errors, missing props, failed assertions
    Evidence: .sisyphus/evidence/task-18-component-tests.txt

  Scenario: Build succeeds with all components
    Tool: Bash
    Preconditions: All components created
    Steps:
      1. Run `cd apps/frontend && npx vite build`
      2. Assert exit code 0, no TypeScript errors
    Expected Result: Clean production build
    Failure Indicators: Type errors, missing imports, build failure
    Evidence: .sisyphus/evidence/task-18-build-check.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): chat UI components with shadcn/ui and Vitest tests`
  - Files: `apps/frontend/src/components/**`
  - Pre-commit: `cd apps/frontend && npx vitest run`

- [x] 19. Frontend Zustand Stores + SSE Hook

  **What to do**:
  - **TDD: Write tests FIRST**:
    - `src/stores/__tests__/chatStore.test.ts`: Test addMessage, setLoading, setDepartment, clearMessages, setSessionId actions
    - `src/hooks/__tests__/useSSE.test.ts`: Test SSE connection lifecycle, message parsing, reconnection logic
  - Implement `src/stores/chatStore.ts` (expand from Task 5 skeleton):
    - State: `messages: ChatMessage[]`, `isLoading: boolean`, `department: Department | "auto"`, `sessionId: string`, `agentTrace: AgentTrace | null`
    - Actions: `addMessage`, `updateLastMessage` (for streaming append), `setLoading`, `setDepartment`, `clearMessages`, `setAgentTrace`
    - Middleware: `devtools` (Redux DevTools), `persist` (localStorage for sessionId)
  - Implement `src/hooks/useSSE.ts`:
    - Custom hook: `useSSE(url: string, options: SSEOptions)`
    - Parses SSE events: `data: {"type": "token", "content": "..."}`, `data: {"type": "trace", ...}`, `data: {"type": "done"}`
    - Auto-reconnection with exponential backoff (1s, 2s, 4s, max 30s)
    - Cleanup on unmount (close EventSource)
    - Returns: `{ isConnected, error, connect, disconnect }`
  - Implement `src/hooks/useChat.ts`:
    - Combines chatStore + useSSE into high-level `useChat()` hook
    - `sendMessage(text: string)`: adds user message → starts SSE → streams tokens → adds final assistant message

  **Must NOT do**:
  - Do NOT use WebSocket — SSE only
  - Do NOT implement caching or optimistic updates
  - Do NOT add real API URL yet (use configurable base URL from env)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: State management and hooks are straightforward TypeScript patterns
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: This is logic, not visual

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 14-18)
  - **Blocks**: Task 22 (page assembly)
  - **Blocked By**: Task 5 (frontend scaffolding)

  **References**:

  **External References**:
  - Zustand devtools + persist middleware: https://docs.pmnd.rs/zustand/middlewares
  - EventSource API (SSE): https://developer.mozilla.org/en-US/docs/Web/API/EventSource
  - SSE event format: `data: ...\n\n`

  **WHY Each Reference Matters**:
  - Zustand `persist` middleware enables sessionId survival across page reloads
  - EventSource API handles SSE natively but needs manual reconnection logic for error recovery

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test files: `src/stores/__tests__/chatStore.test.ts`, `src/hooks/__tests__/useSSE.test.ts`
  - [ ] `npx vitest run` → PASS

  **QA Scenarios:**

  ```
  Scenario: Chat store manages messages correctly
    Tool: Bash
    Preconditions: Store tests written
    Steps:
      1. Run `npx vitest run src/stores/__tests__/chatStore.test.ts --reporter=verbose`
      2. Assert addMessage adds to messages array
      3. Assert updateLastMessage appends to last message content (for streaming)
      4. Assert clearMessages empties array
      5. Assert department defaults to "auto"
    Expected Result: All store actions work correctly
    Failure Indicators: Wrong state after action, missing actions
    Evidence: .sisyphus/evidence/task-19-store-tests.txt

  Scenario: SSE hook parses events correctly
    Tool: Bash
    Preconditions: SSE hook tests written with mock EventSource
    Steps:
      1. Run `npx vitest run src/hooks/__tests__/useSSE.test.ts --reporter=verbose`
      2. Assert token events append to message content
      3. Assert trace events update agentTrace
      4. Assert done event stops loading state
    Expected Result: All SSE event types handled correctly
    Failure Indicators: Unparsed events, missing event types
    Evidence: .sisyphus/evidence/task-19-sse-hook-tests.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): Zustand stores, SSE hook, and useChat with TDD`
  - Files: `apps/frontend/src/stores/**`, `apps/frontend/src/hooks/**`, tests
  - Pre-commit: `cd apps/frontend && npx vitest run`

### Wave 4 — Integration (After Wave 3, 6 parallel)

- [x] 20. Supervisor Agent (create_supervisor)

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/agents/test_supervisor.py`:
    - Test Supervisor routes "VPN reset" to IT Support agent
    - Test Supervisor routes "baggage limit" to Airport Ground Services agent
    - Test Supervisor routes "flight delay + credit card refund" to BOTH Airport Ground + Credit Card agents
    - Test Supervisor returns structured output with routing decision + agent responses
    - Test Supervisor handles agent timeout gracefully (one agent fails, others still return)
    - Mock all department agents with FakeListChatModel
  - Implement `app/agents/supervisor.py`:
    - Use `create_supervisor` from `langgraph_supervisor`:
      ```python
      supervisor = create_supervisor(
          agents=[it_agent, legal_agent, credit_card_agent, airport_agent],
          model=llm,
          prompt=SUPERVISOR_SYSTEM_PROMPT,
          output_mode="full_history"
      )
      ```
    - `SUPERVISOR_SYSTEM_PROMPT`: Instructs supervisor to:
      - Analyze user query to determine relevant department(s)
      - Route to single agent for clear single-department queries
      - Route to multiple agents for cross-department queries
      - Synthesize multi-agent responses into coherent answer
    - Compile graph: `supervisor.compile()`
    - Create `SupervisorService` class wrapping the compiled graph:
      - `route_query(query: str, department: Optional[Department]) -> SupervisorResult`
      - If department is explicitly specified → route directly (skip supervisor analysis)
      - If department is "auto" or None → let supervisor decide
      - Return: `SupervisorResult(answer, departments_used, agent_traces, confidence)`

  **Must NOT do**:
  - Do NOT hand-roll supervisor logic — use `create_supervisor` from `langgraph-supervisor`
  - Do NOT implement weighted routing or load balancing
  - Do NOT allow supervisor to create new agents dynamically

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core orchestration component — Supervisor pattern with multi-agent routing
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 21-25)
  - **Blocks**: Tasks 21, 28
  - **Blocked By**: Task 17 (department agents)

  **References**:

  **Pattern References**:
  - `langgraph-supervisor` README: `create_supervisor(agents, model, prompt, output_mode)` — exact API
  - langgraph-supervisor-py examples on GitHub

  **External References**:
  - `langgraph_supervisor` package: https://github.com/langchain-ai/langgraph-supervisor-py
  - `create_supervisor` parameters: `agents`, `model`, `tools` (optional), `prompt`, `output_mode` ("last_message" or "full_history"), `include_agent_name`

  **WHY Each Reference Matters**:
  - `create_supervisor` is the official LangGraph way to build supervisor patterns — using anything else would be non-standard
  - `output_mode="full_history"` is needed to capture all agent interactions for the trace panel

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/agents/test_supervisor.py`
  - [ ] `pytest tests/agents/test_supervisor.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Single-department routing
    Tool: Bash
    Preconditions: Supervisor with 4 mock department agents
    Steps:
      1. Invoke supervisor with "How do I reset my VPN password?"
      2. Assert only IT Support agent was invoked (check trace)
      3. Assert response is relevant to VPN
    Expected Result: Query routed to IT Support only
    Failure Indicators: Multiple agents invoked, wrong department, no response
    Evidence: .sisyphus/evidence/task-20-single-dept-routing.txt

  Scenario: Cross-department routing
    Tool: Bash
    Preconditions: Supervisor with 4 mock department agents
    Steps:
      1. Invoke supervisor with "My flight was delayed and I need a refund on my credit card"
      2. Assert both Airport Ground Services AND Credit Card agents were invoked
      3. Assert response synthesizes both agents' answers
    Expected Result: Two departments invoked, merged response
    Failure Indicators: Only one department, no synthesis, timeout
    Evidence: .sisyphus/evidence/task-20-cross-dept-routing.txt

  Scenario: Explicit department skips supervisor routing
    Tool: Bash
    Preconditions: Supervisor service
    Steps:
      1. Call `route_query("anything", department=Department.LEGAL)`
      2. Assert only Legal agent invoked (no supervisor analysis)
    Expected Result: Direct routing when department specified
    Failure Indicators: Supervisor still analyzes query
    Evidence: .sisyphus/evidence/task-20-explicit-dept.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): Supervisor agent with create_supervisor and multi-department routing`
  - Files: `app/agents/supervisor.py`, `tests/agents/test_supervisor.py`
  - Pre-commit: `pytest tests/agents/test_supervisor.py`

- [x] 21. Chat Service + SSE Streaming API

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/routers/test_chat.py`:
    - Test `POST /api/v1/chat` returns ChatResponse with answer, department, sources
    - Test `POST /api/v1/chat/stream` returns SSE stream with token events
    - Test API requires X-API-Key header
    - Test invalid request body returns 422 with error details
    - Test conversation is saved to PostgreSQL after response
    - Use `httpx.AsyncClient` with `app=app` for async tests
  - Implement `app/services/chat.py`:
    - `ChatService` class orchestrating the full flow:
      1. Get or create conversation (ConversationRepository)
      2. Load conversation history (last 10 messages)
      3. Route query through SupervisorService
      4. Save response + trace to conversation
      5. Return ChatResponse
    - `chat_stream(request)` → async generator yielding SSE events:
      - `{"type": "token", "content": "..."}` — streaming tokens
      - `{"type": "sources", "data": [...]}` — retrieval sources
      - `{"type": "trace", "data": {...}}` — agent routing trace
      - `{"type": "done"}` — end of stream
  - Implement `app/routers/chat.py`:
    - `POST /api/v1/chat` → synchronous (waits for full response)
    - `POST /api/v1/chat/stream` → SSE streaming (`StreamingResponse(media_type="text/event-stream")`)
    - Both endpoints: validate request → call ChatService → return response
    - SSE format: `data: {json}\n\n` per event
    - SSE heartbeat: send `data: {"type": "heartbeat"}\n\n` every 15 seconds to keep connection alive

  **Must NOT do**:
  - Do NOT use WebSocket — SSE with `StreamingResponse` only
  - Do NOT buffer the entire response before streaming
  - Do NOT skip conversation persistence — every chat must be saved

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex integration — SSE streaming + service orchestration + persistence
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 20, 22-25)
  - **Blocks**: Tasks 26, 27
  - **Blocked By**: Tasks 12 (auth), 13 (conversation repo), 15 (Self-RAG), 20 (Supervisor)

  **References**:

  **Pattern References**:
  - FastAPI StreamingResponse docs — `StreamingResponse(generator(), media_type="text/event-stream")`
  - SSE event format: `data: {json}\n\n`

  **External References**:
  - FastAPI streaming: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
  - SSE specification: event stream format with `data:` prefix

  **WHY Each Reference Matters**:
  - `StreamingResponse` is FastAPI's built-in SSE support — no external library needed
  - SSE heartbeat prevents Nginx `proxy_read_timeout` from killing long-running agent queries

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/routers/test_chat.py`
  - [ ] `pytest tests/routers/test_chat.py` → PASS (5+ tests)

  **QA Scenarios:**

  ```
  Scenario: Chat endpoint returns structured response
    Tool: Bash
    Preconditions: Backend running with all services
    Steps:
      1. Run `curl -s -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -H "X-API-Key: test-key" -d '{"message": "What is the baggage weight limit?", "department": "airport_ground"}'`
      2. Assert status 200
      3. Assert response has fields: answer, department, sources, confidence
      4. Assert department == "airport_ground"
      5. Assert sources is non-empty array
    Expected Result: Structured response with answer, sources, confidence
    Failure Indicators: 500 error, missing fields, empty sources
    Evidence: .sisyphus/evidence/task-21-chat-response.txt

  Scenario: SSE stream delivers incremental tokens
    Tool: Bash
    Preconditions: Backend running
    Steps:
      1. Run `curl -sN -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -H "X-API-Key: test-key" -d '{"message": "What is the VPN setup process?"}' --max-time 30 | head -10`
      2. Assert output contains multiple `data:` lines
      3. Assert first event has `"type": "token"`
      4. Assert last event has `"type": "done"`
    Expected Result: Multiple SSE events with incremental tokens
    Failure Indicators: Single large response (not streaming), missing done event, timeout
    Evidence: .sisyphus/evidence/task-21-sse-stream.txt

  Scenario: Chat without API key returns 401
    Tool: Bash
    Preconditions: Backend running
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message": "test"}'`
      2. Assert status code 401
    Expected Result: 401 Unauthorized
    Failure Indicators: 200 (auth bypassed), 500 (crash)
    Evidence: .sisyphus/evidence/task-21-no-auth.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): chat service with SSE streaming API and TDD`
  - Files: `app/services/chat.py`, `app/routers/chat.py`, `tests/routers/test_chat.py`
  - Pre-commit: `pytest tests/routers/test_chat.py`

- [x] 22. Frontend Chat Page Assembly + Agent Trace Panel

  **What to do**:
  - **TDD: Write tests FIRST**:
    - `src/pages/__tests__/ChatPage.test.tsx`: Test page renders chat components, department selector, trace panel
    - Test trace panel shows agent routing info when agentTrace is set in store
    - Test trace panel is collapsible
  - Implement `src/pages/ChatPage.tsx`:
    - Layout: sidebar (department selector) + main (chat messages + input) + right panel (agent trace, collapsible)
    - Wire up components from Task 18 with hooks/stores from Task 19
    - Pass `useChat().sendMessage` to `ChatInput.onSend`
    - Pass `chatStore.messages` to `ChatMessageList`
    - Pass `chatStore.agentTrace` to `AgentTracePanel`
  - Implement `src/components/AgentTracePanel.tsx`:
    - Collapsible right panel showing:
      - Supervisor routing decision (which departments selected)
      - Agents invoked (with status: running/completed/failed)
      - Retrieval sources per agent (department badge + document title + relevance score)
      - Iteration count (Self-RAG iterations)
      - Confidence score
    - Use shadcn/ui `Collapsible`, `Badge`, `Accordion` components
  - Update `src/App.tsx` to render `ChatPage` as the main content

  **Must NOT do**:
  - Do NOT add page routing — single page only
  - Do NOT add conversation history sidebar (out of scope)
  - Do NOT make real API calls yet (mock data for testing — real wiring in Task 27)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Page layout assembly with responsive design and interactive panels
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Layout design, responsive patterns, interactive panel UX
  - **Skills Evaluated but Omitted**:
    - `playwright`: No E2E tests

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 20-21, 23-25)
  - **Blocks**: Tasks 26, 27
  - **Blocked By**: Tasks 18 (chat components), 19 (stores + hooks)

  **References**:

  **External References**:
  - shadcn/ui Collapsible: https://ui.shadcn.com/docs/components/collapsible
  - shadcn/ui Accordion: https://ui.shadcn.com/docs/components/accordion

  **WHY Each Reference Matters**:
  - Collapsible is needed for the agent trace panel toggle
  - Accordion for expandable agent details within the trace panel

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `src/pages/__tests__/ChatPage.test.tsx`
  - [ ] `npx vitest run` → PASS

  **QA Scenarios:**

  ```
  Scenario: Chat page renders all sections
    Tool: Bash
    Preconditions: Page components assembled
    Steps:
      1. Run `npx vitest run src/pages/__tests__/ChatPage.test.tsx --reporter=verbose`
      2. Assert chat input is rendered
      3. Assert department selector is rendered with 5 options (4 departments + auto)
      4. Assert agent trace panel toggle exists
    Expected Result: All three sections present in DOM
    Failure Indicators: Missing sections, render errors
    Evidence: .sisyphus/evidence/task-22-chat-page-render.txt

  Scenario: Production build succeeds with full page
    Tool: Bash
    Preconditions: All frontend components + page assembled
    Steps:
      1. Run `cd apps/frontend && npx vite build`
      2. Assert exit code 0
      3. Assert dist/ directory contains index.html and JS bundles
    Expected Result: Clean build with no errors
    Failure Indicators: TypeScript errors, missing imports
    Evidence: .sisyphus/evidence/task-22-build-check.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): chat page with agent trace panel and department selector`
  - Files: `apps/frontend/src/pages/**`, `apps/frontend/src/components/AgentTracePanel.tsx`
  - Pre-commit: `cd apps/frontend && npx vitest run`

- [x] 23. ARQ Worker Setup + Background Tasks

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/workers/test_worker.py`:
    - Test worker function registration and discovery
    - Test `ingest_department_task(department)` calls IngestionService
    - Test `evaluate_conversation_task(session_id)` calls EvaluationService
    - Test task failure handling (retry, dead letter)
    - Mock Redis with `fakeredis`
  - Implement `app/workers/`:
    - `worker.py`: ARQ worker main configuration
      - Redis pool connection (DB 1, separate from docstore)
      - Worker settings: `max_jobs=5`, `job_timeout=300` (5 min for ingestion)
      - Function registry: `ingest_department_task`, `evaluate_conversation_task`
    - `tasks.py`: Task implementations
      - `ingest_department_task(ctx, department: str)` — calls IngestionService
      - `evaluate_conversation_task(ctx, session_id: str)` — calls EvaluationService (Task 24)
    - `__init__.py` with task exports
  - Create worker entrypoint: `python -m arq app.workers.worker.WorkerSettings`
  - Add worker service to Docker Compose entrypoint

  **Must NOT do**:
  - Do NOT use Celery — ARQ only
  - Do NOT share Redis DB with docstore (use DB 1 for ARQ, DB 0 for docstore)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: ARQ worker configuration with async patterns and task management
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 20-22, 24-25)
  - **Blocks**: Tasks 24, 25
  - **Blocked By**: Tasks 2 (settings), 9 (ChromaDB — for ingestion tasks)

  **References**:

  **External References**:
  - ARQ docs: https://arq-docs.helpmanual.io/ — WorkerSettings, function registration, job configuration
  - ARQ Redis configuration: separate connection pool, DB number selection

  **WHY Each Reference Matters**:
  - ARQ is our chosen async task queue — must configure correctly for FastAPI async ecosystem
  - Separate Redis DB prevents key collisions between ARQ jobs and docstore data

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/workers/test_worker.py`
  - [ ] `pytest tests/workers/test_worker.py` → PASS

  **QA Scenarios:**

  ```
  Scenario: Worker starts and registers tasks
    Tool: Bash
    Preconditions: Redis running, worker module implemented
    Steps:
      1. Run `python -c "from app.workers.worker import WorkerSettings; print([f.__name__ for f in WorkerSettings.functions])"`
      2. Assert output contains "ingest_department_task" and "evaluate_conversation_task"
    Expected Result: Both task functions registered
    Failure Indicators: Import error, missing function registration
    Evidence: .sisyphus/evidence/task-23-worker-registration.txt

  Scenario: Task can be enqueued via ARQ
    Tool: Bash
    Preconditions: Redis running
    Steps:
      1. Run Python script that creates ARQ pool and enqueues `ingest_department_task` with department="it_support"
      2. Assert job is enqueued (returns job object with job_id)
    Expected Result: Job enqueued successfully with job_id
    Failure Indicators: Connection error, serialization error
    Evidence: .sisyphus/evidence/task-23-enqueue-task.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): ARQ worker with ingestion and evaluation background tasks`
  - Files: `app/workers/*.py`, `tests/workers/test_worker.py`
  - Pre-commit: `pytest tests/workers/test_worker.py`

- [x] 24. RAGAS Evaluation Service + Endpoint

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/services/test_evaluation.py`:
    - Test `EvaluationService.evaluate_conversation(session_id)` returns RAGASMetrics
    - Test evaluation stores results in PostgreSQL via EvaluationResult model
    - Test evaluation handles conversations with no sources gracefully
    - Mock RAGAS metrics computation (don't make real LLM calls)
  - Implement `app/services/evaluation.py`:
    - `EvaluationService` class
    - `evaluate_conversation(session_id: str) -> EvaluationResult`:
      1. Load conversation messages from ConversationRepository
      2. Extract question-answer-context triples from messages
      3. Compute RAGAS metrics: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
      4. Store results in PostgreSQL
      5. Return metrics
    - Use RAGAS library with Azure OpenAI as evaluator LLM
  - Implement `app/routers/evaluation.py`:
    - `POST /api/v1/evaluation/trigger` — enqueues evaluation job via ARQ, returns job_id
    - `GET /api/v1/evaluation/results/{session_id}` — returns stored evaluation results
    - `GET /api/v1/evaluation/results/{session_id}/status` — returns job status (pending/running/completed/failed)

  **Must NOT do**:
  - Do NOT build evaluation UI — API endpoints only
  - Do NOT run evaluation synchronously in the API — always via ARQ background job
  - Do NOT evaluate in real-time during chat — post-hoc evaluation only

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: RAGAS integration + async evaluation pipeline + API endpoint design
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 20-23, 25)
  - **Blocks**: None
  - **Blocked By**: Tasks 13 (conversation repo), 23 (ARQ worker)

  **References**:

  **External References**:
  - RAGAS docs: https://docs.ragas.io/ — evaluate function, metrics (faithfulness, answer_relevancy, context_precision, context_recall)
  - RAGAS with Azure OpenAI: https://docs.ragas.io/en/latest/howtos/customisations/azure-openai.html

  **WHY Each Reference Matters**:
  - RAGAS provides standard metrics for RAG evaluation — the industry standard for measuring RAG quality
  - Azure OpenAI integration requires specific LLM wrapper configuration in RAGAS

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/services/test_evaluation.py`
  - [ ] `pytest tests/services/test_evaluation.py` → PASS

  **QA Scenarios:**

  ```
  Scenario: Trigger evaluation and retrieve results
    Tool: Bash
    Preconditions: Backend running, conversation exists in DB
    Steps:
      1. Run `curl -s -X POST http://localhost:8000/api/v1/evaluation/trigger -H "X-API-Key: test-key" -H "Content-Type: application/json" -d '{"session_id": "test-session"}'`
      2. Assert response has `job_id` field
      3. Wait 30 seconds for background job
      4. Run `curl -s http://localhost:8000/api/v1/evaluation/results/test-session -H "X-API-Key: test-key"`
      5. Assert response has metrics: faithfulness, answer_relevancy, context_precision, context_recall
      6. Assert all metrics are floats between 0.0 and 1.0
    Expected Result: Evaluation triggered, results retrievable with valid metrics
    Failure Indicators: Missing job_id, evaluation never completes, metrics out of range
    Evidence: .sisyphus/evidence/task-24-ragas-evaluation.txt

  Scenario: Evaluation of empty conversation returns graceful error
    Tool: Bash
    Preconditions: Backend running, no conversation with given session_id
    Steps:
      1. Run `curl -s -X POST http://localhost:8000/api/v1/evaluation/trigger -H "X-API-Key: test-key" -H "Content-Type: application/json" -d '{"session_id": "nonexistent"}'`
      2. Assert status 404 or response indicates no conversation found
    Expected Result: Graceful error, not 500 crash
    Failure Indicators: 500 Internal Server Error, unhandled exception
    Evidence: .sisyphus/evidence/task-24-empty-conversation.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): RAGAS evaluation service with background job and API endpoints`
  - Files: `app/services/evaluation.py`, `app/routers/evaluation.py`, `tests/services/test_evaluation.py`
  - Pre-commit: `pytest tests/services/test_evaluation.py`

- [x] 25. Seed Data Ingestion via ARQ

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/services/test_seed.py`:
    - Test `SeedService.seed_all_departments()` enqueues 4 ingestion jobs (one per department)
    - Test `SeedService.check_seed_status()` returns status per department
    - Test seeding is skipped if collections already have documents
  - Implement `app/services/seed.py`:
    - `SeedService` class
    - `seed_all_departments()`:
      1. Check each department collection in ChromaDB
      2. If empty → enqueue `ingest_department_task` via ARQ
      3. If already populated → skip (idempotent)
      4. Return dict of {department: "seeded" | "skipped"}
    - `check_seed_status()` → returns document counts per department collection
  - Implement `scripts/seed.py`:
    - CLI: `python scripts/seed.py` — triggers seeding for all departments
    - Waits for all jobs to complete with progress display
  - Update Docker Compose `seed` service to run `python scripts/seed.py` on first startup

  **Must NOT do**:
  - Do NOT re-ingest if documents already exist — idempotent seeding
  - Do NOT block API startup waiting for seeding — seed runs as separate container

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Orchestration of ingestion across 4 departments with idempotency logic
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 20-24)
  - **Blocks**: Task 26 (Docker production config)
  - **Blocked By**: Tasks 16 (ingestion service), 23 (ARQ worker)

  **References**:

  **Pattern References**:
  - Task 16 IngestionService — this task orchestrates Task 16's service across all departments
  - Task 23 ARQ worker — this task enqueues jobs via ARQ

  **WHY Each Reference Matters**:
  - This is the glue between ingestion and ARQ — must correctly use both APIs

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/services/test_seed.py`
  - [ ] `pytest tests/services/test_seed.py` → PASS

  **QA Scenarios:**

  ```
  Scenario: Seed all departments from empty state
    Tool: Bash
    Preconditions: ChromaDB empty, Redis running, synthetic docs in data/
    Steps:
      1. Run `python scripts/seed.py`
      2. Assert exit code 0
      3. Check ChromaDB collections: all 4 departments have documents
      4. Run `python -c "from app.services.seed import SeedService; print(SeedService().check_seed_status())"`
      5. Assert all 4 departments show document counts > 0
    Expected Result: All 4 departments seeded with documents
    Failure Indicators: Empty collections, failed ingestion, timeout
    Evidence: .sisyphus/evidence/task-25-seed-all.txt

  Scenario: Re-seeding skips already populated departments
    Tool: Bash
    Preconditions: All departments already seeded
    Steps:
      1. Record document counts per department
      2. Run `python scripts/seed.py` again
      3. Record new document counts
      4. Assert counts unchanged (no duplicates)
    Expected Result: Seed script reports "skipped" for all departments
    Failure Indicators: Document counts increased, duplicate documents
    Evidence: .sisyphus/evidence/task-25-seed-idempotent.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): seed service for initial knowledge base population`
  - Files: `app/services/seed.py`, `scripts/seed.py`, `tests/services/test_seed.py`
  - Pre-commit: `pytest tests/services/test_seed.py`

### Wave 5 — Production Polish (After Wave 4, 5 parallel)

- [x] 26. Docker Compose Production Config + Nginx SSE

  **What to do**:
  - Finalize `docker-compose.yml` with production-ready configuration:
    - All services with health checks:
      - `api`: `curl -f http://localhost:8000/api/v1/health`
      - `worker`: custom health check script (check ARQ connection)
      - `redis`: `redis-cli ping`
      - `chromadb`: `curl -f http://localhost:8000/api/v1/heartbeat`
      - `postgres`: `pg_isready`
      - `nginx`: `curl -f http://localhost/api/v1/health`
      - `frontend`: `curl -f http://localhost:3000`
    - Proper `depends_on` with `condition: service_healthy` for startup ordering
    - Resource limits (memory, CPU) per service
    - Restart policies: `unless-stopped` for all services
    - Named volumes for persistence: `chroma_data`, `postgres_data`, `redis_data`
  - Finalize Nginx config:
    - Verify `proxy_buffering off` for `/api/v1/chat/stream`
    - Verify `proxy_read_timeout 300s`
    - Add `X-Accel-Buffering: no` header for SSE routes
    - CORS headers for frontend→API
    - Gzip compression for non-streaming routes
  - Create `docker-compose.dev.yml` override:
    - Volume mounts for hot reload (backend + frontend)
    - Debug ports exposed
    - `PYTHONDONTWRITEBYTECODE=1` for cleaner dev

  **Must NOT do**:
  - Do NOT add Kubernetes manifests
  - Do NOT add CI/CD pipeline configs
  - Do NOT expose database ports externally in production compose

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Production Docker orchestration with health checks and networking
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 27-30)
  - **Blocks**: Task 30 (.env.example)
  - **Blocked By**: Tasks 4 (Docker skeleton), 21 (Chat API), 22 (Frontend), 25 (Seed)

  **References**:

  **Pattern References**:
  - Task 4 Docker skeleton — this task finalizes what Task 4 started
  - Nginx SSE proxy pattern from Metis research

  **WHY Each Reference Matters**:
  - Must build on Task 4's skeleton, not replace it — add health checks, depends_on, resource limits

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: All services start and become healthy
    Tool: Bash
    Preconditions: All images built, .env configured
    Steps:
      1. Run `docker compose up -d`
      2. Wait up to 120 seconds
      3. Run `docker compose ps --format json | python3 -c "import sys,json; services = [json.loads(l) for l in sys.stdin]; healthy = [s for s in services if 'healthy' in s.get('Health','') or s.get('State','')=='running']; print(f'{len(healthy)}/{len(services)} healthy')"`
      4. Assert all 8 services healthy/running
    Expected Result: 8/8 services healthy within 120 seconds
    Failure Indicators: Service stuck in "starting", health check fails, dependency deadlock
    Evidence: .sisyphus/evidence/task-26-docker-healthy.txt

  Scenario: SSE streaming works through Nginx proxy
    Tool: Bash
    Preconditions: All services healthy, data seeded
    Steps:
      1. Run `curl -sN -X POST http://localhost/api/v1/chat/stream -H "X-API-Key: test-key" -H "Content-Type: application/json" -d '{"message": "Hello"}' --max-time 30 | head -5`
      2. Assert output contains multiple `data:` lines (not one buffered response)
      3. Assert response headers include `Content-Type: text/event-stream`
    Expected Result: Incremental SSE events through Nginx, not buffered
    Failure Indicators: Single large response, timeout, Nginx 502
    Evidence: .sisyphus/evidence/task-26-sse-through-nginx.txt

  Scenario: Persistence survives container restart
    Tool: Bash
    Preconditions: Services running with seeded data
    Steps:
      1. Query IT Support knowledge base — assert results
      2. Run `docker compose down && docker compose up -d`
      3. Wait for healthy
      4. Query IT Support again — assert same results (data persisted)
    Expected Result: Data survives restart via Docker volumes
    Failure Indicators: Empty results after restart, lost conversations
    Evidence: .sisyphus/evidence/task-26-persistence.txt
  ```

  **Commit**: YES
  - Message: `feat(docker): production Docker Compose with health checks, Nginx SSE, persistence`
  - Files: `docker-compose.yml`, `docker-compose.dev.yml`, `nginx/nginx.conf`
  - Pre-commit: `docker compose config --quiet`

- [x] 27. Frontend ↔ Backend Integration + SSE Wiring

  **What to do**:
  - Wire frontend SSE hook to actual backend endpoints:
    - Update `src/hooks/useChat.ts` to call `POST /api/v1/chat/stream` via EventSource/fetch
    - Configure API base URL from Vite env: `VITE_API_BASE_URL` (defaults to `/api/v1`)
    - Handle SSE event types: token → append to message, sources → display citations, trace → update trace panel, done → stop loading
  - Wire frontend components to real data:
    - ChatPage sends department from DepartmentSelector to chat API
    - AgentTracePanel displays real trace data from SSE events
    - SourceList displays real sources from SSE events
  - Handle error states:
    - API unreachable → show error toast
    - SSE connection lost → auto-reconnect with exponential backoff
    - 401 → show "Invalid API key" error
  - Add `X-API-Key` header to all API calls (configurable via `VITE_API_KEY` env)

  **Must NOT do**:
  - Do NOT add authentication UI — API key is configured via env var
  - Do NOT add offline mode or service worker caching

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Frontend-backend integration with SSE streaming and UI state management
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Error state handling UX, loading states, toast notifications
  - **Skills Evaluated but Omitted**:
    - `playwright`: QA will use Playwright but as part of Final Verification, not this task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 26, 28-30)
  - **Blocks**: None
  - **Blocked By**: Tasks 21 (Chat API), 22 (Frontend page)

  **References**:

  **Pattern References**:
  - Task 19 useSSE hook — this task wires it to real endpoints
  - Task 21 SSE event format — must match backend event types

  **WHY Each Reference Matters**:
  - SSE event types must exactly match backend format: `{"type": "token", "content": "..."}`

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: End-to-end chat in browser
    Tool: Playwright (playwright skill)
    Preconditions: All services running via Docker Compose, data seeded
    Steps:
      1. Navigate to http://localhost
      2. Select "IT Support" from department dropdown
      3. Type "How do I reset my VPN password?" in chat input
      4. Click send button
      5. Wait for response to appear (streaming tokens visible)
      6. Assert response message appears with VPN-related content
      7. Assert source cards appear below response
      8. Click agent trace panel toggle
      9. Assert trace panel shows "it_support" as department
      10. Screenshot full page
    Expected Result: Full chat flow works: input → stream → response with sources + trace
    Failure Indicators: No response, SSE connection error, empty trace, missing sources
    Evidence: .sisyphus/evidence/task-27-e2e-chat.png

  Scenario: Error handling for failed connection
    Tool: Playwright (playwright skill)
    Preconditions: Frontend running, backend stopped
    Steps:
      1. Navigate to http://localhost
      2. Type "test" and send
      3. Assert error state is shown (toast or inline error)
      4. Assert chat input is re-enabled after error
    Expected Result: Graceful error display, no frozen UI
    Failure Indicators: Infinite loading, frozen input, unhandled error
    Evidence: .sisyphus/evidence/task-27-error-handling.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): wire chat UI to backend SSE API with error handling`
  - Files: `apps/frontend/src/hooks/**`, `apps/frontend/src/pages/**`
  - Pre-commit: `cd apps/frontend && npx vitest run`

- [x] 28. LangGraph Checkpointing with AsyncPostgresSaver

  **What to do**:
  - **TDD: Write tests FIRST** in `tests/agents/test_checkpointing.py`:
    - Test conversation state persists across graph invocations (multi-turn)
    - Test agent remembers previous messages in session
    - Test different session_ids have isolated state
    - Mock PostgreSQL with SQLite or in-memory for tests
  - Implement checkpointing in `app/agents/supervisor.py` (modify existing):
    - Import `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio`
    - Create saver: `AsyncPostgresSaver.from_conn_string(postgres_dsn)`
    - Pass `checkpointer=saver` to supervisor graph compilation
    - Thread config: use `session_id` as `thread_id` for `configurable={"thread_id": session_id}`
  - Update `app/services/chat.py`:
    - Pass `session_id` as thread config to supervisor invocation
    - This enables multi-turn conversations where the agent remembers context

  **Must NOT do**:
  - Do NOT use MemorySaver (not persistent across restarts)
  - Do NOT add checkpoint cleanup/pruning (out of scope)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: LangGraph checkpointing integration with PostgreSQL async driver
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 26, 27, 29, 30)
  - **Blocks**: None
  - **Blocked By**: Tasks 7 (PostgreSQL models), 20 (Supervisor), 21 (Chat service)

  **References**:

  **External References**:
  - LangGraph Checkpointing docs: https://langchain-ai.github.io/langgraph/concepts/persistence/
  - `AsyncPostgresSaver`: `langgraph-checkpoint-postgres` package
  - Thread-based conversation isolation: `configurable={"thread_id": session_id}`

  **WHY Each Reference Matters**:
  - `AsyncPostgresSaver` is the production-grade checkpointer — stores graph state in PostgreSQL
  - `thread_id` is how LangGraph isolates conversation states between different users/sessions

  **Acceptance Criteria**:

  **TDD:**
  - [ ] Test file: `tests/agents/test_checkpointing.py`
  - [ ] `pytest tests/agents/test_checkpointing.py` → PASS

  **QA Scenarios:**

  ```
  Scenario: Multi-turn conversation with memory
    Tool: Bash
    Preconditions: All services running, data seeded
    Steps:
      1. Send message: "What is the baggage weight limit?" with session_id="multi-turn-test"
      2. Assert response about baggage
      3. Send follow-up: "What about oversized items?" with same session_id
      4. Assert response references previous context (knows we're talking about baggage)
    Expected Result: Agent remembers previous question in same session
    Failure Indicators: Agent doesn't reference previous context, treats as new conversation
    Evidence: .sisyphus/evidence/task-28-multi-turn.txt

  Scenario: Different sessions are isolated
    Tool: Bash
    Preconditions: All services running
    Steps:
      1. Send "What is the VPN setup?" to session "session-A"
      2. Send "What is the baggage limit?" to session "session-B"
      3. Send follow-up "Tell me more" to session "session-A"
      4. Assert session-A follow-up relates to VPN (not baggage)
    Expected Result: Sessions have isolated conversation states
    Failure Indicators: Session-A references session-B's context
    Evidence: .sisyphus/evidence/task-28-session-isolation.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): LangGraph checkpointing with AsyncPostgresSaver for multi-turn conversations`
  - Files: `app/agents/supervisor.py` (modified), `app/services/chat.py` (modified), `tests/agents/test_checkpointing.py`
  - Pre-commit: `pytest tests/agents/test_checkpointing.py`

- [x] 29. Comprehensive README + Architecture Docs

  **What to do**:
  - Create `README.md` (project root) — the portfolio centerpiece:
    - **Header**: Project name, one-line description, tech badges (Python, TypeScript, LangGraph, FastAPI, React, Docker)
    - **Architecture Diagram**: ASCII or Mermaid diagram showing:
      - User → Nginx → FastAPI → Supervisor Agent → Department Agents (×4)
      - Each agent → Hybrid Retriever → ChromaDB + BM25
      - Self-RAG loop: Retrieve → Generate → Critique → Refine
      - Data flow: SSE streaming back to React frontend
    - **Features**: Bullet list of key capabilities
    - **Tech Stack**: Table with technology, purpose, and version
    - **Quick Start**: `docker compose up -d` + wait + demo commands
    - **Architecture Deep Dive**: Detailed explanation of each component
    - **API Reference**: Key endpoints with curl examples
    - **Configuration**: All env vars documented
    - **Development**: How to run locally without Docker
    - **Testing**: How to run backend + frontend tests
    - **Evaluation**: How to trigger RAGAS evaluation
    - **Project Structure**: Directory tree with descriptions
    - **Design Decisions**: Why LangGraph over Autogen, why SSE over WebSocket, why Chroma over Milvus, etc.
  - Create `docs/architecture.md`:
    - Detailed component diagrams (Mermaid)
    - Data flow diagrams
    - Agent interaction sequence diagrams
  - Create `docs/api-reference.md`:
    - All endpoints documented with request/response examples
  - Create `docs/deployment.md`:
    - Docker Compose setup, environment configuration, volume management

  **Must NOT do**:
  - Do NOT write generic documentation — every section must be specific to this project
  - Do NOT include implementation details that would change (focus on architecture and usage)
  - Do NOT add auto-generated API docs (FastAPI has /docs built-in)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Technical documentation writing — the portfolio presentation layer
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 26-28, 30)
  - **Blocks**: None
  - **Blocked By**: All previous tasks (needs full understanding of implemented system)

  **References**:

  **Pattern References**:
  - All previous tasks — README documents the complete system
  - User's stated goal: "文档写清晰一点" (write documentation clearly)

  **WHY Each Reference Matters**:
  - README quality directly impacts portfolio impression — this is what interviewers see first

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: README has all required sections
    Tool: Bash
    Preconditions: README written
    Steps:
      1. Run `grep "## Architecture" README.md` — assert present
      2. Run `grep "## Quick Start" README.md` — assert present
      3. Run `grep "## Tech Stack" README.md` — assert present
      4. Run `grep "## API Reference" README.md` — assert present
      5. Run `grep "docker compose" README.md` — assert present (quick start uses Docker)
      6. Run `grep "## Design Decisions" README.md` — assert present
      7. Run `wc -w README.md` — assert > 2000 words (comprehensive)
    Expected Result: All required sections present, >2000 words
    Failure Indicators: Missing section, too short, generic content
    Evidence: .sisyphus/evidence/task-29-readme-sections.txt

  Scenario: Architecture diagram is present and valid
    Tool: Bash
    Preconditions: docs/architecture.md written
    Steps:
      1. Run `grep "mermaid" docs/architecture.md` — assert Mermaid diagrams present
      2. Assert at least 2 diagrams (system overview + agent interaction)
    Expected Result: Mermaid diagrams for architecture visualization
    Failure Indicators: No diagrams, text-only architecture description
    Evidence: .sisyphus/evidence/task-29-architecture-diagrams.txt
  ```

  **Commit**: YES
  - Message: `docs: comprehensive README, architecture diagrams, API reference, deployment guide`
  - Files: `README.md`, `docs/*.md`
  - Pre-commit: N/A

- [x] 30. .env.example + Setup Scripts

  **What to do**:
  - Finalize `.env.example` with ALL required environment variables, grouped and documented:
    ```
    # === Azure OpenAI ===
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    AZURE_OPENAI_API_KEY=your-api-key
    AZURE_OPENAI_DEPLOYMENT=gpt-4o
    AZURE_OPENAI_API_VERSION=2024-06-01
    
    # === Embedding ===
    EMBEDDING_PROVIDER=local  # "local" (bge-base-en-v1.5) or "azure"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002  # only if EMBEDDING_PROVIDER=azure
    
    # === ChromaDB ===
    CHROMA_HOST=chromadb
    CHROMA_PORT=8000
    
    # === Redis ===
    REDIS_URL=redis://redis:6379
    
    # === PostgreSQL ===
    POSTGRES_DSN=postgresql+asyncpg://postgres:postgres@postgres:5432/airline_rag
    
    # === API ===
    API_KEY=your-secret-api-key
    API_HOST=0.0.0.0
    API_PORT=8000
    
    # === Logging ===
    LOG_LEVEL=INFO
    
    # === Optional: LangSmith (observability) ===
    # LANGCHAIN_TRACING_V2=true
    # LANGCHAIN_API_KEY=your-langsmith-key
    ```
  - Create `scripts/setup.sh`:
    - Check prerequisites (Docker, Docker Compose)
    - Copy `.env.example` to `.env` if not exists
    - Prompt user for Azure OpenAI credentials
    - Run `docker compose build`
    - Run `docker compose up -d`
    - Wait for health checks
    - Run seeding
    - Print success message with demo commands
  - Create `Makefile` with common commands:
    - `make up` — docker compose up
    - `make down` — docker compose down
    - `make test` — run backend + frontend tests
    - `make seed` — run seed script
    - `make evaluate` — trigger evaluation
    - `make logs` — tail all service logs

  **Must NOT do**:
  - Do NOT hardcode any real credentials
  - Do NOT add Terraform or cloud-specific deployment scripts

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Configuration files and shell scripts — straightforward
  - **Skills**: []
  - **Skills Evaluated but Omitted**: None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 26-29)
  - **Blocks**: None
  - **Blocked By**: Task 26 (Docker Compose final config)

  **References**:

  **Pattern References**:
  - Task 2 settings — .env.example must list ALL variables used by Settings class

  **WHY Each Reference Matters**:
  - .env.example is the single source of truth for configuration — must match Settings

  **Acceptance Criteria**:

  **QA Scenarios:**

  ```
  Scenario: Setup script runs end-to-end
    Tool: Bash
    Preconditions: Docker installed, .env not yet created
    Steps:
      1. Run `bash scripts/setup.sh` (with test credentials)
      2. Assert .env file created
      3. Assert Docker images built
      4. Assert services start (docker compose ps shows running)
    Expected Result: Full setup from scratch with one command
    Failure Indicators: Script error, missing .env, build failure
    Evidence: .sisyphus/evidence/task-30-setup-script.txt

  Scenario: .env.example has all required variables
    Tool: Bash
    Preconditions: .env.example finalized
    Steps:
      1. Extract variable names from .env.example: `grep "^[A-Z]" .env.example | cut -d= -f1`
      2. Check that Settings class references all these variables
      3. Verify no undocumented env vars used in code but missing from .env.example
    Expected Result: .env.example is complete and matches Settings class
    Failure Indicators: Missing variable, undocumented env var
    Evidence: .sisyphus/evidence/task-30-env-completeness.txt

  Scenario: Makefile targets work
    Tool: Bash
    Preconditions: Makefile created
    Steps:
      1. Run `make -n up` — assert it shows docker compose command
      2. Run `make -n test` — assert it shows pytest and vitest commands
      3. Run `make -n seed` — assert it shows seed script command
    Expected Result: All make targets defined and correct
    Failure Indicators: Missing target, wrong command
    Evidence: .sisyphus/evidence/task-30-makefile.txt
  ```

  **Commit**: YES
  - Message: `feat: .env.example, setup script, and Makefile for developer experience`
  - Files: `.env.example`, `scripts/setup.sh`, `Makefile`
  - Pre-commit: `bash -n scripts/setup.sh`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`, `npx vitest run`, linter. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp). Verify all Python imports use correct `langchain-*` sub-packages (not `langchain` meta-package).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill for frontend)
  Start from `docker compose up -d`. Wait for all services healthy. Execute EVERY QA scenario from EVERY task. Test cross-department query (flight delay + credit card refund). Test SSE streaming in browser. Test agent trace panel shows routing. Test RAGAS evaluation trigger. Test dual embedding mode switch. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no Milvus code, no `langchain` meta-package, no `InMemoryStore` in production paths, no JWT auth. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Order | Message | Key Files | Pre-commit Check |
|-------|---------|-----------|-----------------|
| 1 | `feat: project scaffolding and monorepo structure` | pyproject.toml, package.json, docker-compose.yml skeleton, .env.example | N/A |
| 2 | `feat(backend): core settings, logging, and Pydantic schemas` | app/core/*, app/schemas/* | `pytest tests/core/` |
| 3 | `feat(backend): dual embedding factory with TDD` | app/core/embeddings.py, tests/core/test_embeddings.py | `pytest tests/core/test_embeddings.py` |
| 4 | `feat(backend): ChromaDB repository and batch operations` | app/repositories/vectorstore.py, tests/repositories/ | `pytest tests/repositories/` |
| 5 | `feat(backend): Redis docstore and document chunking pipeline` | app/core/docstore.py, app/services/chunking.py | `pytest tests/core/ tests/services/` |
| 6 | `feat(backend): hybrid retriever (BM25 + Vector EnsembleRetriever)` | app/services/retrieval.py | `pytest tests/services/test_retrieval.py` |
| 7 | `feat(backend): Self-RAG StateGraph with critique loop` | app/agents/self_rag.py | `pytest tests/agents/test_self_rag.py` |
| 8 | `feat(backend): department agents and Supervisor with LangGraph` | app/agents/*.py | `pytest tests/agents/` |
| 9 | `feat(backend): chat API with SSE streaming + auth middleware` | app/routers/chat.py, app/middleware/ | `pytest tests/routers/` |
| 10 | `feat(backend): document ingestion service + seed data` | app/services/ingestion.py, scripts/ingest.py, data/ | `pytest tests/services/test_ingestion.py` |
| 11 | `feat(frontend): React chat UI with SSE + agent trace panel` | apps/frontend/src/** | `npx vitest run` |
| 12 | `feat(infra): ARQ worker, RAGAS evaluation, LangGraph checkpoints` | app/workers/*, app/services/evaluation.py | `pytest tests/workers/ tests/services/test_evaluation.py` |
| 13 | `feat(docker): production Docker Compose with Nginx + health checks` | docker-compose.yml, nginx.conf, Dockerfile* | `docker compose up -d && docker compose ps` |
| 14 | `docs: comprehensive README, architecture diagrams, setup guide` | README.md, docs/* | N/A |

---

## Success Criteria

### Verification Commands
```bash
# All Docker services running
docker compose up -d && sleep 60 && docker compose ps | grep -c "healthy\|running"
# Expected: 8 (api, worker, redis, chromadb, postgres, nginx, frontend, seed-complete)

# Health check
curl -s http://localhost/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'"
# Expected: exit 0

# Single department query (IT Support)
curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" -H "X-API-Key: test-key" \
  -d '{"message": "How do I reset my VPN password?", "department": "it_support"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['department']=='it_support'; assert len(d['sources'])>0"
# Expected: exit 0, response with IT Support sources

# Cross-department query
curl -s -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" -H "X-API-Key: test-key" \
  -d '{"message": "My flight was delayed and I need a refund on my credit card"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d.get('departments',[]))>=2"
# Expected: exit 0, multiple departments involved

# SSE streaming
curl -sN http://localhost/api/v1/chat/stream \
  -H "X-API-Key: test-key" \
  -d '{"message": "What is the baggage weight limit?"}' \
  --max-time 30 | head -5
# Expected: multiple "data: ..." lines with incremental tokens

# Backend tests
cd apps/backend && python -m pytest tests/ -v --tb=short
# Expected: all green, 0 failures

# Frontend tests
cd apps/frontend && npx vitest run
# Expected: all green, 0 failures

# RAGAS evaluation trigger
curl -s -X POST http://localhost/api/v1/evaluation/trigger \
  -H "X-API-Key: test-key" \
  -d '{"session_id": "test-session"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('job_id') is not None"
# Expected: non-null job_id

# Dual embedding mode
docker compose exec api python -c "from app.core.embeddings import get_embedding_model; m = get_embedding_model(); print(type(m).__name__)"
# Expected: "HuggingFaceBgeEmbeddings" (default) or "AzureOpenAIEmbeddings" (when EMBEDDING_PROVIDER=azure)
```

### Final Checklist
- [ ] All "Must Have" items present and verified
- [ ] All "Must NOT Have" items absent (no Milvus, no langchain meta, no InMemoryStore, no JWT, no CI/CD)
- [ ] 8 Docker services running with health checks
- [ ] Backend pytest: 0 failures
- [ ] Frontend vitest: 0 failures
- [ ] Single-department query returns relevant answer with sources
- [ ] Cross-department query invokes multiple agents
- [ ] SSE streaming delivers incremental tokens
- [ ] Agent trace panel visible in frontend
- [ ] RAGAS evaluation triggers successfully
- [ ] README includes architecture diagram + setup guide + demo walkthrough
- [ ] All dependency versions pinned
- [ ] No `as any`, `@ts-ignore`, empty catches, or console.log in production code
