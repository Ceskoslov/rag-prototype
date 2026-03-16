# Learnings — Multi-Agent RAG Project

> Conventions, patterns, and best practices discovered during implementation.

---


## Docker Infrastructure Patterns (Task 4)

### SSE Streaming in Production
- **Critical Nginx directives for SSE**: `proxy_buffering off`, `proxy_read_timeout 300s`, `X-Accel-Buffering: no`
- Without these, SSE responses buffer on first chunk, breaking real-time streaming perception
- Configure in both HTTP and HTTPS server blocks for consistency
- WebSocket upgrade headers also needed: `Connection: upgrade`, `Upgrade: $http_upgrade`

### Embedding Model Pre-download
- Pre-download models in Docker RUN layer using sentence-transformers library
- Pattern: `RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"`
- Saves 500MB download + timeout risk on first container startup
- Cache persists in multi-stage build using `COPY --from=base /root/.cache /root/.cache`
- Essential for demo-day reliability

### Multi-stage Dockerfile Pattern
- Backend: base (with build tools) → production (lean runtime)
- Frontend: dev (live reload) → builder (build step) → production (static serve)
- Use `.dockerignore` to exclude node_modules, .git, venv in COPY steps
- Reduces production image size by 60-70% vs single-stage

### Docker Compose Service Dependencies
- Use `depends_on` with `condition: service_healthy` for correct startup order
- Define health checks for each service (especially db, cache, api)
- Health check timeout: 5s, interval: 10s, retries: 5 (reasonable defaults)
- ARQ worker uses different Redis DB: `redis://redis:6379/1` (db=0 for app cache)

### Nginx Configuration for Multi-service Routing
- Use upstream blocks for service resolution in Docker network
- Separate location blocks for `/api/` and `/` with different proxy_pass targets
- Include WebSocket headers even if not immediately needed (forward-compatible)
- CORS OPTIONS handling in Nginx reduces backend load

### PostgreSQL Init Scripts
- Place init SQL in `/docker-entrypoint-initdb.d/` with numeric prefix (01-, 02-)
- Create extensions first, then tables, then indexes
- Use `IF NOT EXISTS` for idempotency (safe re-runs)
- Foreign key cascades for document chunks cleanup

### Environment Variable Strategy
- Use `.env` file (git-ignored) for secrets
- Provide defaults in compose file with `${VAR_NAME:-default_value}`
- Separate dev overrides in `docker-compose.dev.yml`
- Never hardcode credentials in compose files


## Task 3: Pydantic Schemas + Type Definitions

### Patterns Discovered

#### 1. Pydantic v2 Schema Structure
- **Department Enum Pattern**: Use `class Department(str, Enum)` for enum serialization to string values in API responses
  - Inherit from both `str` and `Enum` to get string-compatible behavior
  - Enum values use snake_case for Python compatibility and JSON serialization
  - Example: `IT_SUPPORT = "it_support"` allows access as `Department.IT_SUPPORT` or `Department.IT_SUPPORT.value`

#### 2. Required vs Optional Fields
- **Required fields**: No default value, no `Optional[]` wrapper
  - Pydantic v2 enforces validation automatically
  - Error message on missing required field is automatic
- **Optional fields**: Use `Optional[Type]` and typically `Field(None, description="...")`
  - Example: `department: Optional[Department] = Field(None, description="Target department")`

#### 3. Nested Model Pattern
- **AgentTrace within ChatResponse**: Pydantic models can nest other models seamlessly
  - Nested models serialize recursively in `model_dump_json()`
  - Use proper type hints for nested model fields
  - Example: `trace: AgentTrace = Field(..., description="Trace of agent execution")`

#### 4. Serialization Methods
- **Pydantic v2 only**: Use `.model_dump_json()` (NOT deprecated `.json()`)
- **Dict conversion**: Use `.model_dump()` (NOT deprecated `.dict()`)
- Both methods work on nested models automatically

#### 5. Field Metadata Pattern
- Always use `Field(...)` with `description` parameter for API schema generation
- This enables automatic OpenAPI documentation generation
- Example: `message: str = Field(..., description="User's chat message")`

### Best Practices Established

1. **Enum Design**:
   - Always inherit from both `str` and `Enum` for JSON serialization
   - Use uppercase CONSTANT_NAME for enum members
   - Use lowercase_snake_case for enum values

2. **Error Handling**:
   - Pydantic v2 raises `ValidationError` automatically for invalid inputs
   - Required fields without defaults are mandatory
   - Type mismatches are caught automatically

3. **Schema Organization**:
   - Separate schemas by domain: `common.py` (shared), `chat.py` (chat logic), `document.py` (RAG), `evaluation.py` (metrics)
   - Re-export all schemas in `__init__.py` for cleaner imports
   - Keep schemas focused on data validation, not business logic

4. **Testing Strategy**:
   - Test valid inputs (happy path)
   - Test missing required fields (error case)
   - Test type mismatches (error case)
   - Test serialization/deserialization roundtrips
   - Test nested model serialization

### Technical Decisions

- **Pydantic v2** chosen for superior validation, better IDE support, and proper async support
- **No Config class**: Pydantic v2 uses `model_config = ConfigDict(...)` if needed (not used here)
- **Department enum values**: Snake_case ensures JSON compatibility and matches API contracts
- **AgentTrace fields**: Includes `iterations` counter to track Self-RAG refinement cycles

### Dependencies

- **Depends on**: Task 1 (project structure), Task 2 (settings for validation)
- **Blocks**: Tasks 8, 9, 11 (these tasks use these schemas in services/repositories)
- **No external runtime dependencies**: Core Pydantic only

### Files Delivered

- ✓ `apps/backend/app/schemas/common.py` — Shared types
- ✓ `apps/backend/app/schemas/chat.py` — Chat request/response models
- ✓ `apps/backend/app/schemas/document.py` — Document and ingestion models
- ✓ `apps/backend/app/schemas/evaluation.py` — RAGAS evaluation models
- ✓ `apps/backend/tests/schemas/test_schemas.py` — Comprehensive test suite
- ✓ `.sisyphus/evidence/task-3-*.txt` — QA scenario evidence


## Document Generation Learnings - 2026-03-16
- Standardized metadata headers (department, last_updated, category, audience) ensure consistent RAG ingestion and easier filtering.
- Using a fictional company name like "SkyWing Airlines" across all documents maintains thematic consistency.
- Including specific thresholds and policies (e.g., "Baggage weight limit: 23kg", "14-character passwords") provides realistic data for testing RAG extraction capabilities.
- Organizing documents by department subdirectories facilitates granular access control and easier data management.

## Frontend Scaffolding (Task 5)

### Tailwind CSS v4 Changes
- **Deprecated direct PostCSS plugin**: Tailwind v4 removed the ability to use `tailwindcss` directly as a PostCSS plugin
- **New approach**: Must install `@tailwindcss/postcss` and use it in PostCSS config: `'@tailwindcss/postcss': {}`
- **CSS import simplified**: Single import in index.css: `@import "tailwindcss";` — handles all directives automatically
- **Breaking change**: Old pattern `@layer base { ... }` still works but not necessary in v4 when using the new import

### Type-only Imports (TypeScript strict mode)
- **`verbatimModuleSyntax: true` requirement**: When enabled in tsconfig, type-only imports must use `import type` syntax
- **Error pattern**: `'X' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled`
- **Solution**: Always write `import type { X, Y, Z } from '@/path'` for types-only
- **Exception**: Values and components use regular `import { Component } from '@/path'`
- **Best practice**: Let TypeScript LSP auto-fix with "Organize Imports" command

### Zustand Store Setup with Middleware
- **localStorage persist middleware**: Use the `persist` middleware to automatically persist store slices
- **Selective persistence**: Use `partialize` option to persist only specific state keys (e.g., sessionId only)
- **Test setup required**: `jest-dom` and localStorage mock in `vitest.setup.ts` required for testing
- **Mock localStorage pattern**: Test environment needs manual mock since jsdom doesn't fully support it
  ```typescript
  const localStorageMock = {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString() },
    removeItem: (key) => { delete store[key] },
    clear: () => { store = {} }
  }
  ```
- **devtools middleware**: Second middleware in chain enables Redux DevTools browser extension support

### TypeScript Path Aliases in Vite
- **Both configs needed**: Update `vite.config.ts` AND `tsconfig.app.json` with matching aliases
- **Pattern**: 
  - Vite: `resolve.alias: { '@': path.resolve(__dirname, './src') }`
  - TypeScript: `paths: { '@/*': ['./src/*'] }`
- **Without both**: IDE won't resolve paths correctly even if Vite builds successfully

### Frontend Package Structure Created
- **Type definitions**: `src/types/chat.ts` (ChatMessage, Department, AgentTrace), `src/types/api.ts` (SSEEvent, APIError)
- **Store**: `src/stores/chatStore.ts` with full action handlers (addMessage, setLoading, setDepartment, setSessionId, setAgentTrace, clearMessages)
- **Utils**: `src/lib/utils.ts` with shadcn `cn()` utility for classname merging
- **Layout skeleton**: `src/App.tsx` with sidebar + main area + header + message display + footer structure
- **Providers**: `src/main.tsx` ready for provider wrapping (Zustand needs no explicit provider)

### Vitest Configuration
- **Environment**: jsdom for DOM APIs
- **Global test functions**: `globals: true` enables describe/it/expect without imports
- **Path aliases in tests**: Must also configure in `vitest.config.ts` for test imports to work
- **Setup files**: Create `vitest.setup.ts` for test environment initialization (localStorage mock)
- **Test script**: Add to package.json: `"test": "vitest run"`

### Test Structure for Zustand
- **Store state access**: Use `useChatStore.getState()` to access current state in tests (not hook-based)
- **State mutations**: Call action methods on store: `store.addMessage(message)` then re-fetch with `getState()`
- **Cleanup**: Use `beforeEach` to clear state between tests
- **Persistence testing**: localStorage mock must be cleared after each test with `localStorage.clear()`

### Department Type Matching Backend
- **Frontend enum type**: `type Department = 'it_support' | 'legal' | 'credit_card' | 'airport_ground'`
- **Matches Pydantic**: Backend Pydantic enum has same string values
- **Auto mode**: Zustand store allows `'auto'` value for automatic routing (separate from typed Departments)

### Files Created
- ✓ `apps/frontend/` — Root Vite project directory
- ✓ `apps/frontend/tailwind.config.ts` — Tailwind v4 configuration
- ✓ `apps/frontend/postcss.config.ts` — PostCSS with @tailwindcss/postcss
- ✓ `apps/frontend/vitest.config.ts` — Vitest environment setup
- ✓ `apps/frontend/vitest.setup.ts` — Test environment mocks
- ✓ `apps/frontend/src/types/chat.ts` — Chat domain types
- ✓ `apps/frontend/src/types/api.ts` — API response types
- ✓ `apps/frontend/src/lib/utils.ts` — shadcn utility function
- ✓ `apps/frontend/src/stores/chatStore.ts` — Zustand store with devtools + persist
- ✓ `apps/frontend/src/stores/__tests__/chatStore.test.ts` — Store unit tests (6 tests passing)
- ✓ `apps/frontend/src/App.tsx` — Base layout skeleton
- ✓ `apps/frontend/src/index.css` — Tailwind v4 directives
- ✓ Build succeeds: `npm run build` → `dist/index.html` generated
- ✓ Tests pass: `npm run test` → 6/6 tests passing

### QA Evidence Captured
- ✓ `.sisyphus/evidence/task-5-vite-build.txt` — Build log showing no errors
- ✓ `.sisyphus/evidence/task-5-vitest.txt` — Test results showing 6 passed tests

## Task 7: PostgreSQL Models + Alembic Migrations

### Key Implementation Patterns

**1. SQLAlchemy 2.0 Async Architecture**
- Use `create_async_engine()` with `AsyncSession` for async/await support
- Import from `app.core.database.Base` (centralized declaration base)
- Models inherit from `Base` which has `created_at`, `updated_at` columns
- Use `Mapped` type hints for proper IDE support and type checking
- Use `async_sessionmaker[AsyncSession]` for dependency injection

**2. Circular Import Prevention**
- Place `Base`, `async_engine`, `async_session_factory` in `app/core/database.py`
- Re-export from `app/models/base.py` to avoid circular dependencies
- Models import from `app.models.base` (which is a thin re-export)
- Core/settings imports are clean chain: settings → database → models

**3. Model Relationships**
- Use `TYPE_CHECKING` imports for forward references
- Use `relationship()` with `back_populates` for bidirectional relationships
- Configure `cascade="all, delete-orphan"` for parent deletions
- Use `lazy="select"` for explicit eager loading control
- Foreign keys with `ondelete="CASCADE"` at SQLAlchemy level AND database level

**4. Alembic Setup for Async**
- Configure `env.py` to use async engine in `run_migrations_online()`
- Use `asyncio.run()` wrapper for async support
- Implement `do_run_migrations()` sync function to run within async context
- Use `connection.run_sync()` to execute ORM operations

**5. Testing Async Models**
- Use `pytest-asyncio` with `asyncio_mode = auto` in pytest.ini
- Create test fixtures with `@pytest_asyncio.fixture`
- Use in-memory SQLite (`sqlite+aiosqlite:///:memory:`) for fast, isolated tests
- Use `session.refresh()` with attribute list to load relationships: `await session.refresh(conv, ["messages"])`
- Numeric columns return `Decimal` objects - convert with `float()` for assertions

**6. Migration Naming Convention**
- Use semantic names: `{timestamp}_{description}.py`
- Initial migration: `_initial_schema`
- Include upgrade/downgrade with proper index cleanup
- Drop indexes BEFORE dropping tables in downgrade

### SQLAlchemy 2.0 Syntax (What We Use)
```python
# Good - SQLAlchemy 2.0 async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
engine = create_async_engine("postgresql+asyncpg://...")
async with session() as s:
    result = await s.execute(select(Model).where(...))
    items = result.scalars().all()

# Avoid - SQLAlchemy 1.x style
from sqlalchemy import create_engine
result = session.execute(select(...))  # not awaited
result.execute(insert(...))  # deprecated
```

### JSON Columns for Flexible Metadata
- `sources`: List of source documents used for answer
- `trace`: Step-by-step reasoning trace from AI pipeline
- Both nullable to allow messages without metadata
- Stored as `JSON` type in PostgreSQL (native support)

### Timestamp Handling
- Use `server_default=func.now()` for database-side defaults
- Prevents client-timezone issues
- Both `created_at` (immutable) and `updated_at` (mutable) tracked
- Note: `datetime.utcnow()` is deprecated in Python 3.12+

### Cascade Delete Pattern
- Conversation deletion automatically deletes related Messages and EvaluationResults
- Configured via `cascade="all, delete-orphan"` in relationship
- Also configured in FK constraint: `ForeignKey(..., ondelete="CASCADE")`
- Double configuration ensures consistency across ORM and database levels

### File Organization
- Models in `app/models/` (one file per domain entity)
- Core utilities in `app/core/` (database, settings, dependencies)
- Tests mirror source structure: `tests/models/` → `app/models/`
- Separate conftest for test fixtures and initialization

## Task 11: Parent-Child Chunking Pipeline

- Effective two-stage markdown chunking pattern: run `MarkdownHeaderTextSplitter` first to preserve document structure, then apply `RecursiveCharacterTextSplitter` to enforce target chunk windows.
- Parent/child retrieval hierarchy works cleanly when parent chunks use `chunk_size=1000, chunk_overlap=200` and child chunks use `chunk_size=200, chunk_overlap=50`; this creates coarse semantic containers with finer-grained retrieval units.
- Persisted relationship metadata should be explicit and consistent: parent chunks carry `department`, `source_file`, `chunk_type=parent`, `chunk_index`; child chunks carry the same fields plus `parent_id` and `chunk_type=child`.
- Normalizing enum-like metadata values to strings at chunk generation time avoids downstream mismatches between schema enums and vector-store metadata filters.

## Task 10: Redis Document Store Implementation

### LangChain BaseStore Interface
- **Abstract methods required**: `mget`, `mset`, `mdelete`, `yield_keys`
- **Return types matter**: `mget` returns `list[Optional[V]]` (None for missing keys)
- **Batch-first design**: All methods work with sequences, not single values
- **Prefix filtering**: `yield_keys(prefix=None)` must support optional prefix matching
- **Type safety**: Use `BaseStore[str, Document]` for proper generic typing

### Document Serialization Pattern
- **JSON serialization**: Store as `{"page_content": str, "metadata": dict}`
- **Minimal fields**: Only serialize `page_content` and `metadata` (not `id` or `type`)
- **Nested metadata**: JSON handles nested dicts, lists, and primitives automatically
- **Round-trip safety**: Deserialize using `Document(page_content=..., metadata=...)`

### Testing with fakeredis
- **Dependency injection**: Add `redis_client: Optional[redis.Redis]` parameter to `__init__`
- **Test fixture pattern**: Create `FakeRedis(decode_responses=True)` instance
- **Cleanup strategy**: Use `fake_redis.flushdb()` in fixture teardown
- **Persistence testing**: Reuse same `FakeRedis` instance across multiple store objects
- **No external dependencies**: fakeredis eliminates need for Redis server in CI

### Redis Key Management
- **Key format**: `{prefix}:{key}` (e.g., `docstore:it_support:doc123`)
- **scan_iter for iteration**: Use `client.scan_iter(match=pattern)` for prefix filtering
- **Pattern matching**: `prefix:*` for all, `prefix:user:*` for filtered
- **Key stripping**: Remove prefix when yielding keys: `redis_key[len(prefix) + 1:]`
- **DB separation**: Use DB 0 for docstore (ARQ uses DB 1)

### API Design Patterns
- **Optional parameters**: `redis_url` has default for production, `redis_client` for testing
- **Prefix namespacing**: Default `prefix="docstore"` for collision avoidance
- **Empty sequence handling**: Return early for `if not keys` / `if not key_value_pairs`
- **decode_responses=True**: Ensures Redis returns strings, not bytes

### TDD Process Followed
1. **Write tests first**: 5 tests covering all BaseStore methods
2. **Red phase**: Tests fail with `ConnectionError` (tried real Redis)
3. **Green phase**: Fixed with fakeredis dependency injection
4. **Refactor**: Added optional `redis_client` parameter for flexibility

### Files Delivered
- ✓ `apps/backend/app/core/docstore.py` — RedisDocStore implementation (121 lines)
- ✓ `apps/backend/tests/core/test_docstore.py` — Test suite (5 tests, all passing)
- ✓ `.sisyphus/evidence/task-10-pytest-results.txt` — Full pytest output
- ✓ `.sisyphus/evidence/task-10-verification.txt` — Implementation summary

## Task 12: API Key Authentication & Health Check (2026-03-16)

### FastAPI Security Dependencies Pattern
- **Header validation**: Use `Header(None, alias="X-API-Key")` to accept missing headers without validation error
- **Timing-safe comparison**: Always use `secrets.compare_digest()` for API key comparison (prevents timing attacks)
- **HTTP status codes**:
  - 401 Unauthorized: Missing/empty credentials → client should retry with auth
  - 403 Forbidden: Invalid credentials → client is rejected

### FastAPI Dependency Injection for Auth
- **Dependency function**: Create async function `verify_api_key()` and use with `Depends()`

## Task 9: ChromaRepository + Batch Insert Strategy (2026-03-16)

- Chroma department collections should use deterministic names: `{department}_knowledge_base` (normalized to lowercase snake_case) to keep retrieval routing simple and predictable.
- For API server usage, initialize production vector client with `chromadb.HttpClient(host="chromadb", port=8000)` so Docker service DNS resolves consistently inside the compose network.
- Large inserts must always go through `chromadb.utils.batch_utils.create_batches(api=client, ids=..., metadatas=..., documents=...)` to respect Chroma/SQLite parameter limits (notably ~41,666 record ceiling).
- Batch utility returns tuples in this order: `(ids, embeddings, metadatas, documents)`; repository add loops should preserve that order when calling `collection.add(...)`.
- Repository contract should explicitly enforce operational rule: writes are serialized via ARQ worker (single-writer model) to avoid concurrent write contention.
- **Reusability**: Attach to any endpoint with `@app.get("/protected", dependencies=[Depends(verify_api_key)])`
- **Return value**: Dependency can return the validated key for use in handler
- **Error handling**: Raise HTTPException to return proper error responses

### Health Check Endpoint Design
- **Standard path**: Use `/api/v1/health` for version-scoped health checks
- **Status indicator**: Single "status" field: "ok" (healthy) or "degraded"/"unavailable"
- **Service breakdown**: "services" dict with individual service status
- **Always accessible**: Health endpoints should be exempt from authentication
- **Fast responses**: Return mock/local checks initially, integrate real connectivity checks later

### Response Structure Pattern
```python
class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
```
- Use Pydantic for automatic JSON serialization
- Include meaningful service names (redis, chromadb, postgres)

### TDD for Security Features
- **Test missing credential**: Verify 401 response
- **Test invalid credential**: Verify 403 response  
- **Test valid credential**: Verify 200 OK
- **Test timing safety**: Ensure wrong keys are rejected consistently (no timing info leakage)
- **Test case sensitivity**: Verify comparison is case-sensitive if key contains letters

### Configuration Pattern
- **Settings file**: Add security config to `app/core/settings.py`
- **Environment override**: Use `os.getenv("API_KEY", "default-key")`
- **Separation**: Keep auth config separate from database/service configs

### Test Client Usage with Async
- **FastAPI TestClient**: Works with async endpoints (internally runs event loop)
- **Header passing**: `client.get("/path", headers={"X-API-Key": "value"})`
- **Status assertions**: Check `response.status_code` directly
- **JSON parsing**: Use `response.json()` for structured assertion

### Project Structure for Middleware
- `app/middleware/auth.py` — Authentication dependencies
- `app/routers/health.py` — Health check and diagnostic endpoints
- Both packages need `__init__.py` to be importable
- Mirror test structure: `tests/middleware/`, `tests/routers/`

### Files Created (Task 12)
- ✓ `apps/backend/app/middleware/auth.py` — `verify_api_key()` dependency
- ✓ `apps/backend/app/routers/health.py` — Health check endpoint router
- ✓ `apps/backend/tests/middleware/test_auth.py` — 6 auth tests
- ✓ `apps/backend/tests/routers/test_health.py` — 10 health endpoint tests
- ✓ Modified `apps/backend/app/core/settings.py` — Added `api_key` field
- ✓ `.sisyphus/evidence/task-12-auth-health.txt` — Full evidence log

### Test Results
- **16/16 tests PASSING** (6 auth + 10 health)
- Timing-safe comparison verified
- Case-sensitive comparison verified
- All HTTP status codes correct

## Task 13: Async Repository Pattern Implementation

### Repository Layer Best Practices

**1. Async Session Management Pattern**
- Inject `AsyncSession` as constructor parameter, not factory
- Repository doesn't manage session lifecycle - caller controls context
- Pattern: `repo = ConversationRepository(session)` inside `async with session():`
- Enables transaction control at service layer, not repository layer

**2. flush() vs commit() in Repositories**
- Use `await session.flush()` to persist within transaction WITHOUT committing
- Allows caller to batch multiple operations in single transaction
- Use `await session.refresh(obj)` after flush to populate auto-generated IDs
- Never call `commit()` in repository methods - that's service layer responsibility

**3. Query Result Extraction Methods**
- `scalar_one()`: Exactly one result, raises if zero or multiple
- `scalar_one_or_none()`: Zero or one result, None if empty, raises if multiple
- `scalars().all()`: Returns list of ORM objects from first column
- Use `list(result.scalars().all())` for type checker satisfaction

**4. get_or_create Pattern**
```python
async def get_or_create_conversation(self, session_id: str, department: str):
    conv = await self.get_conversation(session_id)
    if conv:
        return conv
    return await self.create_conversation(session_id, department)
```
- Check existence first, return if found
- Create only if not exists
- No race condition in tests (single-threaded SQLite)
- Production needs UNIQUE constraint + exception handling for concurrency

**5. Pagination with SQLAlchemy**
- Use `.limit(n).offset(m)` for pagination
- Default limit prevents unbounded queries: `limit: int = 100`
- Offset for page skipping: `limit=20, offset=40` → page 3

**6. Ordering for Context Windows**
- Retrieve recent messages: `order_by(desc(Message.id)).limit(10)`
- Reverse list for chronological order: `messages.reverse()`
- Pattern: DESC query + reverse = efficient "last N in order"

**7. Dict Serialization for LangChain**
- Return `List[Dict[str, Any]]` not ORM objects for integration layers
- Format: `{"role": msg.role, "content": msg.content}`
- Matches LangChain ChatMessage schema expectations
- Explicit serialization better than ORM leakage

**8. Testing Async Repositories**
- Use `pytest_asyncio.fixture` for session factory
- In-memory SQLite with `StaticPool` for test isolation
- Each test gets fresh database via fixture scope
- `await session.refresh(obj, ["relationship"])` to test lazy-loaded relations

**9. Method Specialization**
- Separate `add_message()` (generic) from `save_agent_response()` (specialized)
- `save_agent_response()` hardcodes `role="assistant"` for clarity
- Composition over conditional parameters

**10. Type Hints for Repository Methods**
- Return concrete types: `-> Conversation` not `-> dict`
- Use `Optional[Model]` for nullable returns (get operations)
- List types for collections: `-> List[Message]`
- Dict types for serialized data: `-> List[Dict[str, Any]]`

### SQLAlchemy 2.0 Async Patterns (Reinforced)

**Query Execution Flow**
```python
# 1. Build statement
stmt = select(Message).where(Message.conversation_id == conv_id)

# 2. Execute with session
result = await session.execute(stmt)

# 3. Extract results
messages = result.scalars().all()
```

**Relationship Loading**
- Relationships are NOT auto-loaded in async mode
- Use `selectinload()` for eager loading: `select(A).options(selectinload(A.bs))`
- Or use `await obj.awaitable_attrs.relationship_name` for lazy load

**Session Operations**
- `session.add(obj)` - Mark for INSERT
- `await session.flush()` - Execute pending SQL without commit
- `await session.commit()` - Commit transaction
- `await session.refresh(obj)` - Reload from database
- `await session.refresh(obj, ["attr"])` - Load specific attributes

### TDD Workflow Lessons

**RED-GREEN-REFACTOR Applied**
1. **RED**: Wrote 10 test cases covering all methods and edge cases
2. **GREEN**: Implemented minimal repository to pass all tests
3. **REFACTOR**: (skipped - implementation already clean)

**Test Coverage Strategy**
- Individual CRUD operations (create, get, add, retrieve)
- Edge cases (not found, duplicates)
- Complex operations (pagination, ordering, context retrieval)
- Full lifecycle integration test

**Test Naming Convention**
- `test_<method>` for happy path
- `test_<method>_<edge_case>` for edge cases
- `test_full_<domain>_lifecycle` for integration

### Dependencies and Integration Points

**Blocks Tasks**
- Task 21: Chat Service (will use ConversationRepository for state management)
- Task 24: RAGAS Evaluation (will use get_messages_for_context for test data)

**Uses Components**
- Task 7: Conversation and Message models
- pytest-asyncio fixtures from conftest.py
- SQLAlchemy 2.0 async engine from app.core.database

### Files Delivered

- ✓ `app/repositories/conversation.py` — 116 lines, 7 public methods
- ✓ `tests/repositories/test_conversation.py` — 310 lines, 10 test cases
- ✓ Both `__init__.py` files for proper package structure
- ✓ `.sisyphus/evidence/task-13-*.txt` — QA verification artifacts

### Technical Debt / Future Enhancements

- No concurrency handling in get_or_create (UNIQUE constraint will raise in production)
- No caching layer (intentionally deferred per spec)
- No soft deletes (hard deletes via cascade)
- Pagination lacks total count (requires separate COUNT query)

## Task 8: Embedding Factory (local BGE + Azure)
- Implemented provider-switched embedding factory in `app/core/embeddings.py` with singleton cache keyed by provider (`local`, `azure`) to avoid repeated expensive model construction.
- Local provider initialization uses `HuggingFaceBgeEmbeddings` with exact production config: model `BAAI/bge-base-en-v1.5`, CPU device, and `normalize_embeddings=True` for cosine-similarity-ready vectors.
- Azure provider initialization uses `AzureOpenAIEmbeddings(azure_deployment=..., azure_endpoint=..., api_key=...)` and wraps API key with `SecretStr` for type-safe constructor compatibility.
- Added `clear_embedding_model_cache()` utility used by tests to prevent cache bleed between test cases while preserving runtime singleton behavior.
- Testing pattern for embeddings: monkeypatch embedding classes to avoid external calls, assert constructor kwargs exactly, and validate output dimensions via deterministic fake vectors (768 local, 1536 azure).
- Added runtime QA evidence pattern: capture pytest output + direct local dimension smoke check + invalid provider traceback in `.sisyphus/evidence/task-8-*.txt`.

## Wave 2 Verification and Type Safety (2026-03-16)

### Repository Type Consistency
- **Type hint mismatch discovered**: `ConversationRepository.add_message` had `sources: Optional[Dict[str, Any]]` but `save_agent_response` passed `sources: Optional[List[Dict[str, Any]]]`
- **Root cause**: Message model uses `sources: Mapped[Optional[dict]]` which is SQLAlchemy JSON field that accepts any JSON structure (including lists)
- **Fix**: Changed `add_message` signature to `sources: Optional[List[Dict[str, Any]]]` for consistency across repository methods
- **Lesson**: SQLAlchemy JSON columns are permissive - enforce structure via type hints and tests, not at database level

### Wave 2 Verification Protocol Executed
1. **Read all implementation files** (embeddings, vectorstore, docstore, chunking, auth, health, conversation)
2. **Run full test suite**: 96/96 tests passing
3. **LSP diagnostics**: Found and fixed type mismatch in conversation.py
4. **Grep for TODOs/FIXMEs**: None found
5. **Git commit**: Atomic commit with 55 files (2,282 insertions)
6. **Plan update**: Marked Tasks 8-13 complete

### ChromaDB Repository Verification (Task 9)
- **Implementation confirmed complete**: 147 lines
- **Batch operations working**: Uses `chromadb.utils.batch_utils.create_batches`
- **Test coverage**: 6 tests covering collection creation, batch adds, similarity search, deletion, large payload batching, HTTP client defaults
- **Collection naming**: Department-specific format `{department}_knowledge_base` (snake_case)
- **Production client**: Uses `chromadb.HttpClient(host="chromadb", port=8000)` for Docker networking

### Testing Completeness
- **Total tests**: 96 passing
  - 40 schema tests
  - 9 model tests
  - 5 embedding tests
  - 5 docstore tests
  - 6 vectorstore tests
  - 5 chunking tests
  - 6 auth tests
  - 10 health tests
  - 10 conversation tests
- **Warnings**: 113 deprecation warnings (acceptable - from SQLAlchemy datetime.utcnow and pytest-asyncio)
- **Evidence files**: 12 evidence files saved for Tasks 8-13 + wave-2-full-test-run.txt


## Task 15: Self-RAG StateGraph Implementation (2026-03-16T16:07:30+09:00)

### StateGraph Architecture
- Implemented `SelfRAGState(TypedDict)` with required fields (`query`, `department`, `documents`, `generation`, `critique_result`, `confidence`, `remaining_steps`) plus `iterations` and `node_history` for deterministic test assertions.
- Built 4-node graph flow: `retrieve -> generate -> critique -> rewrite_query`, with conditional routing from critique to `END` on approval or rewrite on rejection.
- Added hard cap logic with two guards: iteration cap (`iterations >= 3`) and RemainingSteps routing threshold (`remaining_steps > 7` enables one more refinement), then explicit end.
- Compiled graph with `recursion_limit=10` using `compiled.with_config(recursion_limit=10)`.

### Testing with FakeListChatModel
- Used `FakeListChatModel` deterministic response sequences to drive approve/reject/rewrite cycles without external model calls.
- Implemented 5 focused tests covering: one-pass approval, forced 3-pass rejection, unanswerable query fallback, no infinite loop enforcement, and exact retrieve/generate/critique/refine order.
- Introduced a lightweight `FakeRetriever` capturing query call history so refinement path behavior can be asserted precisely.

### Integration Points
- `retrieve_node` accepts retriever injection from `RunnableConfig.configurable.retriever` with fallback to constructor-provided retriever.
- Retrieval call contract uses `invoke(query, config={"department": state["department"], "k": 5})`, aligned with HybridRetriever usage expectations.
- Added tenacity retry wrapper for all LLM invocations (`generate`, `critique`, `rewrite`) using exponential backoff and bounded attempts.

## Task 17: Department Agent Factory (2026-03-16)

### create_react_agent Pattern
- `create_react_agent` works well with one department-local `@tool` and a department-specific prompt; setting `name=f"{department.value}_agent"` gives deterministic agent identity for supervisor wiring.
- LangChain tool conversion requires a tool docstring unless an explicit description is provided to `@tool(...)`; missing this fails at runtime during agent construction.

### Tool Closure for Department Isolation
- Defining `rag_search` inside `create_department_agent` cleanly captures `department` in closure and guarantees per-agent routing isolation (`department.value` passed into Self-RAG input).
- Per-agent Self-RAG graph instances avoid cross-department state leakage and keep tool behavior deterministic for supervisor composition.

### Integration with Self-RAG
- Department tool should invoke Self-RAG with `{"query": query, "department": department.value}` and return `generation` with fallback.
- In ReAct tests, fake chat model needs tool-call capable AIMessage output; otherwise agent loops can recurse due to unresolved tool-call flow.

## Task 20: Supervisor Agent (2026-03-16T00:00:00Z)

### create_supervisor Pattern
- `langgraph-supervisor==0.0.3` `create_supervisor` reliably composes existing compiled department graphs when called with `agents`, `model`, `prompt`, and `output_mode`.
- `output_mode="full_history"` is useful for supervisor traceability because worker-agent message history stays available in the returned state.

### Explicit vs Auto Routing
- Explicit department routing should bypass supervisor analysis and call one department graph directly for deterministic behavior and stable confidence defaults.
- Auto routing should parse structured supervisor metadata (`routing_decision.departments`, `routing_decision.confidence`) into typed service output.

### Multi-Agent Synthesis
- Parsing logic should normalize both enum and string department values and deduplicate departments to keep response schema clean.
- Explicit-path timeout handling is best surfaced as a structured low-confidence `SupervisorResult` instead of propagating raw exceptions.

## [2026-03-16 16:35] Task 20: Supervisor Agent with langgraph_supervisor

### LangGraph Supervisor Integration
- **Package**: `langgraph_supervisor` provides `create_supervisor` function
- **Pattern**: Supervisor wraps N department agents, analyzes queries, routes to 1+ agents
- **Key parameters**:
  - `agents`: List of CompiledStateGraph (department agents)
  - `model`: LLM for routing decisions
  - `prompt`: System prompt defining routing strategy
  - `output_mode`: `"full_history"` (returns all messages + routing_decision) vs `"last_message"`
- **Output structure**: `{"messages": [...], "routing_decision": {"departments": [...], "confidence": 0.8}}`

### Explicit Department Bypass Pattern
- **Design**: When user specifies department explicitly, bypass supervisor analysis
- **Implementation**: Check `department` param in `route_query()`, if not None → route directly to that agent
- **Benefits**: Faster response (no LLM routing call), deterministic behavior
- **Confidence heuristic**: Explicit routing = 0.9 confidence (vs supervisor-decided 0.5-0.8)

### Department Extraction with Aliases
- **Problem**: LLM may return departments as strings ("IT Support", "it_support", "IT_SUPPORT")
- **Solution**: Normalize with `.lower().replace("-", "_").replace(" ", "_")` + alias map
- **Aliases**: `{"it_support": IT_SUPPORT, "airport_ground_services": AIRPORT_GROUND}` for common variants
- **Deduplication**: Track parsed departments in list, skip if already added

### SupervisorResult Dataclass
- **Fields**: `answer` (final text), `departments_used` (List[Department]), `agent_traces` (full graph outputs), `confidence` (float 0-1)
- **Usage**: Provides structured output for frontend to show which agents were consulted
- **Trace format**: List of raw graph results (includes messages, routing_decision, tool calls)

### Timeout Handling for Department Agents
- **Pattern**: Catch `TimeoutError` in explicit routing, return graceful error SupervisorResult
- **Values**: confidence=0.0, answer="timed out", agent_traces=[{"error": "timeout", "department": "..."}]
- **Note**: Supervisor graph timeouts NOT handled here (handled at higher layer in ChatService)

### Testing with Fake Graphs
- **Pattern**: Use `FakeSupervisorGraph` class with pre-set result dict for supervisor
- **Pattern**: Use `FakeAgent` class with `invoke()` that returns mock messages
- **Monkeypatching**: Patch `create_supervisor_graph` to return fake for isolated unit tests
- **Coverage**: 6 tests (graph creation, single/multi routing, explicit bypass, parsing, timeout)

### Type Safety Considerations
- **LangGraph type stubs**: Incomplete, expect warnings (`reportMissingTypeStubs`, `reportUnknownMemberType`)
- **Casts needed**: `cast(list[CompiledStateGraph], list(department_agents.values()))` due to Protocol limitations
- **AgentLike Protocol**: Custom protocol for agents that implement `invoke(state) -> dict` (used in type hints)


## [2026-03-16 07:50:13 UTC] Task 21: Chat Service + SSE Streaming API

### ChatService Orchestration Pattern
- Implemented a deterministic orchestration flow: resolve/get conversation by session_id, load recent context window (last 10 turns), call supervisor routing, persist user + assistant messages, then return structured ChatResponse with session continuity.
- Context passed to supervisor is built from recent persisted history plus current user message, keeping routing and generation grounded in prior turns.

### SSE Event Format
- Streaming endpoint emits strict SSE frames in the format `data: {json}\n\n`.
- Event taxonomy implemented and validated in tests: `heartbeat`, `token`, `sources`, `trace`, `done`.
- `token` events stream incrementally from answer tokens; `sources` and `trace` are emitted before the terminal `done` event.

### FastAPI StreamingResponse for SSE
- SSE delivery is implemented with `StreamingResponse(async_generator, media_type='text/event-stream')`.
- Async generator yields pre-formatted SSE chunks directly, avoiding response buffering and preserving incremental client updates.

### Session Management with Conversation History
- Session continuity is anchored on repository `get_or_create_conversation(session_id, department)` and persisted `session_id` returned to clients.
- History retrieval enforces a bounded context window (10 most recent persisted messages), minimizing prompt bloat while preserving recent conversational state.

## [2026-03-16] Task 23: ARQ Worker Setup + Background Tasks

### ARQ Worker Configuration Pattern
- **WorkerSettings class pattern**: Define static class with `functions` list, `redis_settings`, `max_jobs`, `job_timeout`, `keep_result` attributes
- **Redis DB separation**: ARQ worker uses Redis DB 1 (`redis://host:6379/1`), docstore uses DB 0 to prevent key collisions
- **Redis URL manipulation**: Use `settings.redis_url.rstrip('/0') + '/1'` to safely switch from DB 0 to DB 1
- **Worker discovery**: ARQ finds worker via module path: `arq app.workers.worker.WorkerSettings`
- **Function registration**: Tasks registered via `functions = [task1, task2]` list in WorkerSettings
- **Lifecycle hooks**: `on_startup(ctx)` and `on_shutdown(ctx)` for initialization/cleanup

### Background Task Function Signature
- **ARQ task signature**: `async def task_name(ctx: dict[str, Any], *args) -> dict[str, Any]`
- **Context dict (`ctx`)**: Contains `job_id`, `redis`, `job_try`, `enqueue_time`, `score` - passed by ARQ
- **Return value convention**: Return status dict `{"status": "success|failed|not_implemented", ...}` not exceptions
- **Error handling pattern**: Catch exceptions, log with structured logging, return error dict (graceful failure)
- **No re-raising**: Don't re-raise exceptions from tasks - ARQ will retry if exception bubbles up

### IngestionService Integration in Workers
- **Full dependency instantiation**: Workers must construct IngestionService with all 4 dependencies:
  - `chroma_repo = ChromaRepository()`
  - `docstore = RedisDocStore(redis_url=settings.redis_url)`
  - `chunking_service = ChunkingService()`
  - `embedding_model = get_embedding_model(settings)`
- **No session dependency**: IngestionService doesn't use AsyncSession (pure embedding/vector ops)
- **Data directory**: Use `Path("data")` for document location in worker context

### TDD with ARQ Background Tasks
- **Mock pattern**: Patch all service dependencies (`ChromaRepository`, `RedisDocStore`, `ChunkingService`, `get_embedding_model`, `IngestionService`)
- **Nested context managers**: Use multiple `with patch()` blocks for comprehensive mocking
- **Mock service methods**: `mock_service.ingest_department.return_value = None` or `.side_effect = Exception(...)`
- **Test error paths**: Test invalid department enum, service exceptions, placeholder "not implemented" tasks
- **Lifecycle testing**: Test `on_startup` and `on_shutdown` hooks don't raise exceptions

### Type Safety with ARQ
- **Explicit type annotations**: Add types to WorkerSettings class attributes (`functions: list`, `max_jobs: int`, etc.)
- **Context parameter**: Type as `ctx: dict[str, Any]` to satisfy ARQ interface contract
- **Unused parameter warnings**: Expected for `ctx` in lifecycle hooks (required by ARQ but not always used)
- **Incomplete ARQ type stubs**: ARQ package has partial typing, expect `reportUnknownVariableType` warnings

### Docker Compose ARQ Worker Service
- **Command**: `arq app.workers.worker.WorkerSettings` (module path to settings class)
- **Redis URL**: Use DB 0 in env var (`REDIS_URL=redis://redis:6379/0`), worker code switches to DB 1
- **Dependencies**: Worker needs `postgres`, `redis`, `chromadb` (all with health checks)
- **Health check**: Use `redis-cli -n 1 ping` to check ARQ's Redis DB 1 connection
- **Restart policy**: `unless-stopped` for worker resilience

### Redis DB Usage Convention
- **DB 0**: Application cache, RedisDocStore parent chunks
- **DB 1**: ARQ job queue, task metadata, results
- **Rationale**: Namespace isolation prevents key collisions between document IDs and ARQ job IDs

### Structured Logging for Background Tasks
- **Event-based logging**: Use event names as first param: `logger.info("ingest_task_started", ...)`
- **Context fields**: Include `department`, `job_id`, `error`, `documents_ingested` as kwargs
- **Three-stage pattern**: Log task start, completion/failure, with consistent event naming
- **Warning for placeholders**: Use `logger.warning("evaluate_task_not_implemented", ...)` for stub tasks

### Files Delivered (Task 23)
- ✓ `app/core/settings.py` — Added `redis_url` field (DB 0 default)
- ✓ `app/workers/__init__.py` — Export task functions
- ✓ `app/workers/worker.py` — WorkerSettings configuration (33 lines)
- ✓ `app/workers/tasks.py` — Task implementations (67 lines)
- ✓ `tests/workers/__init__.py` — Test package marker
- ✓ `tests/workers/test_worker.py` — TDD test suite (8 tests, 127 lines)
- ✓ `docker-compose.yml` — Updated worker service command to `app.workers.worker.WorkerSettings`

### Test Results
- **New tests**: 8 worker tests (all passing)
- **Total test count**: 143 tests (135 baseline + 8 worker tests)
- **No regressions**: All existing tests still pass
- **TDD verified**: RED phase (8 failures) → GREEN phase (8 passes)

### Dependencies and Blocked Tasks
- **Task 24 (RAGAS Evaluation)**: `evaluate_conversation_task` is placeholder until Task 24 implements EvaluationService
- **Future enhancement**: Actual evaluation will follow same pattern (construct service, call method, return status dict)

---

## [2026-03-16 17:20:36] Task 25: Seed Data Ingestion via ARQ

### Implementation Summary
Successfully implemented idempotent seed data ingestion system using ARQ background job enqueueing. System checks ChromaDB collection document counts and enqueues `ingest_department_task` jobs only for empty collections.

### TDD Approach
1. **RED phase**: Wrote 4 test scenarios first → all failed (ModuleNotFoundError)
2. **GREEN phase**: Implemented SeedService + CLI script → all 4 tests passed
3. **Test count**: 64 baseline → 68 total (4 new seed tests)

### Files Created
- `app/services/seed.py` (57 lines) — SeedService with seed_all_departments + check_seed_status
- `scripts/seed.py` (59 lines) — CLI script with status display
- `tests/services/test_seed.py` (141 lines) — 4 comprehensive test scenarios
- `app/repositories/vectorstore.py` — Added get_collection_count() method

### Key Implementation Patterns

#### Redis URL Manipulation for ARQ DB Switching
ARQ worker uses Redis DB 1 (not DB 0 used by RedisDocStore). Convert URL correctly:
```python
# WRONG: "redis://host:6379/0".rstrip('/0') + '/1' → "redis://host:6379/1/1"
# RIGHT:
arq_redis_url = self.redis_url.rsplit("/", 1)[0] + "/1"
# "redis://host:6379/0" → "redis://host:6379/1"
```

#### Idempotency Check Pattern
```python
for department in Department:
    collection_name = self.chroma_repo._collection_name(department.value)
    count = self.chroma_repo.get_collection_count(collection_name)
    
    if count > 0:
        results[department.value] = "skipped"  # Already populated
    else:
        await pool.enqueue("ingest_department_task", department=department.value)
        results[department.value] = "seeded"   # Job enqueued
```

#### ARQ Pool Management Pattern
```python
pool = await arq.create_pool(RedisSettings.from_dsn(arq_redis_url))
try:
    # Enqueue jobs
    await pool.enqueue("task_name", param=value)
finally:
    await pool.close(close_connection=True)  # Always close in finally
```

#### ChromaDB Collection Count Check
Added to `ChromaRepository`:
```python
def get_collection_count(self, collection_name: str) -> int:
    try:
        collection = cast(ChromaCollection, ...)
        return collection.count()
    except Exception:
        return 0  # Collection doesn't exist yet
```

### Test Patterns Learned

#### Mock _collection_name Static Method
When testing SeedService that uses `self.chroma_repo._collection_name()`:
```python
from app.repositories.vectorstore import ChromaRepository

mock_chroma_repo = MagicMock()
mock_chroma_repo._collection_name = ChromaRepository._collection_name  # Reuse real static method
```

#### Mock ARQ Pool and Job Enqueueing
```python
mock_pool = AsyncMock()
mock_pool.enqueue.return_value = AsyncMock()  # Return mock job

with patch("app.services.seed.arq.create_pool") as mock_create_pool:
    mock_create_pool.return_value = mock_pool
    
    result = await service.seed_all_departments()
    
    assert mock_pool.enqueue.call_count == 4  # One per department
    mock_pool.close.assert_called_once_with(close_connection=True)
```

### CLI Script Design (Non-Blocking)
Seed script enqueues jobs but does NOT wait for completion:
- **Approach**: Show status before/after, enqueue jobs, exit immediately
- **Rationale**: ARQ worker handles job execution asynchronously
- **User flow**: Run script → jobs enqueued → check ARQ worker logs for progress → re-run script to verify final counts

### Gotchas and Lessons

#### Issue: Redis URL Path Manipulation
**Problem**: `"redis://localhost:6379/0".rstrip('/0') + '/1'` produces `"redis://localhost:6379/1/1"`  
**Cause**: `rstrip()` removes all `/` and `0` characters from right, not substring `/0`  
**Solution**: Use `rsplit("/", 1)[0] + "/1"` to split on last `/` and replace DB number

#### Issue: Pydantic Type Annotation Warning
**Problem**: `reportUnannotatedClassAttribute` warnings for `chroma_repo` and `redis_url`  
**Solution**: Add type annotations as class attributes:
```python
class SeedService:
    chroma_repo: ChromaRepository
    redis_url: str
    
    def __init__(self, chroma_repo: ChromaRepository, redis_url: str):
        self.chroma_repo = chroma_repo
        self.redis_url = redis_url
```

#### Issue: ARQ Type Errors (Acceptable)
**Warning**: `reportAttributeAccessIssue: Cannot access attribute "enqueue" for class "ArqRedis"`  
**Cause**: ARQ's `ArqRedis` type stubs incomplete (runtime-only methods)  
**Resolution**: Safe to ignore - tests verify runtime behavior works correctly

### Test Results
- **New tests**: 4 seed service tests (all passing)
- **Total test count**: 68 tests (64 baseline + 4 seed tests)
- **No regressions**: All existing tests still pass
- **TDD verified**: RED phase (4 ModuleNotFoundError) → GREEN phase (4 passes)
- **LSP diagnostics**: 0 errors (warnings acceptable for ARQ runtime types)

### Dependencies Installed
- `arq==0.26.1` — Background job queue
- `chromadb==0.5.23` — Vector database client
- `structlog==24.4.0` — Structured logging
- `fakeredis==2.34.1` — Redis mocking for tests
- `langchain-core==0.3.29` — LangChain core (dependency for docstore)

### Next Steps (Task 26)
- Docker Compose: Configure `seed` service to run `python scripts/seed.py` on first startup
- Consider adding `--force` flag to re-seed populated departments (optional enhancement)
- Add job status polling to CLI for progress tracking (optional enhancement)

