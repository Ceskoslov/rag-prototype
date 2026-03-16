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
