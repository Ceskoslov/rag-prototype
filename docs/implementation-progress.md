# RAG demo implementation

Each numbered step is committed and pushed separately.

1. Runtime: virtualenv commands, migrations, proxy credentials, HTTP defaults,
   worker checks and explicit offline providers.
2. Correctness: bounded evidence critique and stable passage citations.
3. Indexing: document lifecycle, model fingerprints, cache refresh and multilingual retrieval.
4. Evaluation: independent fixtures, full evidence and real evaluator adapter.
5. Experience: streamed generation, cancellation, sessions, source inspection and document management.
6. Maintenance: optional dependencies, regression CI and deployment validation.

## Validation constraints

The initial environment has no running Docker daemon. Container acceptance
must be recorded separately from config validation and local tests. Mock
providers test wiring only, not model quality.

## Step 1

Compose and development override parse successfully. Backend baseline: 63
passing tests plus the new offline embedding check. Frontend: 36 tests, build
and lint pass. Docker daemon is unavailable and sudo requires a password.

## Step 2

Critique receives the original question and complete numbered passages, uses
validated JSON, and rejects invalid citation numbers. Rejected answers abstain
at the iteration limit. Source responses preserve one stable ID per passage
and full evidence for later evaluation. Regression checks cover three rejected
iterations and multiple passages from one file.

## Step 3

Knowledge-base updates build a shadow Chroma collection, then atomically upsert
the catalog pointer. Failed builds keep the prior snapshot. Re-indexing detects
file deletions and fingerprints embedding configuration plus chunking. Old
parent entries expire after a ten-minute reader grace period; obsolete Chroma
snapshots are collected on subsequent ingestion. BM25 caches refresh when the
active collection changes. CJK bigrams, positive BM25L scores, batched parent
reads and global ranking replace per-base rank comparison. Distance thresholds
are configurable and must be calibrated with the benchmark.

## Step 4

Ragas uses the 0.4 collection metrics and async client factories. References
are supplied independently by exact question; missing reference recall is null.
Historical short snippets are excluded. Stored results include evaluator and
reference provenance. Added a fictional multilingual corpus with distractors,
source labels, independent answers, no-answer and injection cases. Offline
benchmark reports explicitly disclaim model-quality claims.

## Step 5

LangGraph now runs async nodes and emits actual model chunks, progress,
verification and replacement events. Rejected drafts are replaced and the UI
labels in-flight text as unverified. Cancellation closes the model stream;
server heartbeats continue during slow work. Frontend handles premature EOF,
server errors and new session IDs. Added session history, per-answer source
inspection/download, document upload/delete/rebuild and job progress. Sources
record their index snapshot. Traces contain stage timings, first-token latency
and provider-reported graph token usage. Live and ready endpoints are separate;
ready actually probes dependencies. HTTP logs include request IDs and timings
without logging prompts or document bodies.

## Step 6

Base/cloud dependencies no longer install Torch or Ragas. CPU Torch is optional,
and evaluation has its own installation group. Ragas 0.4.3 cannot import with
community 0.4.2 (legacy VertexAI module removed), so the evaluation extra pins
community 0.4.1; a real factory contract check catches this incompatibility.
FastAPI, LangGraph, LangChain core, React, Vite and Tailwind were updated.
TypeScript remains 5.9: current typescript-eslint excludes 7 and TypeScript 7
removes baseUrl. Removed the unsupported shadcn-ui package and unused CLI/forms
dependencies. Fixed the generic lib ignore rule to include frontend API code.

CI covers core/backend regression, evaluator factories, independent retrieval,
SQLite migrations, frontend unit/build/lint, browser contracts and Docker smoke.
Container image inspection discovered that redis:8.1-alpine does not exist;
redis:8.2-alpine was verified instead. Docker installs dependencies without trying
to build the app before source files are copied. Build contexts exclude secrets
and local dependencies. Local Docker startup remains unverified because the
daemon is unavailable; its CI job must be checked after the final push.

## Deferred decisions

- Actual provider quality/latency and reranker comparisons need real credentials
  and representative documents. Offline numbers are wiring regression only.
- ARQ is retained at its current release for compatibility; a queue replacement
  needs a separate migration decision, despite its maintenance-only status.
- OCR/layout parsing, user ACLs, multi-tenancy and alternate storage architecture
  remain product decisions. They are not prerequisites for this local demo.
- Configurable token pricing and production billing attribution are not included.

## Final local validation (2026-10-14)

- With evaluation extra: 82 backend tests pass, including real Ragas factory
  initialization with no provider request.
- Base plus dev: 81 backend tests pass; the optional Ragas factory test is
  explicitly skipped. Neither Torch nor Ragas is installed.
- Frontend: 40 unit tests, lint and production build pass after npm ci.
- Browser: two Playwright workflows pass (chat evidence/new session/document
  lifecycle and premature stream EOF).
- Fictional retrieval benchmark: Recall@6 1.0 and MRR 0.9722 across 19 cases;
  these are offline wiring numbers, not a real-model quality claim.
- Fresh SQLite Alembic upgrade, locked dependency checks, shell syntax and both
  Compose configs pass. Required Redis/Chroma/uv/Nginx image manifests exist.
- No Docker daemon or real provider credentials are available locally. Container
  acceptance and real model quality must be evaluated independently.

## CI follow-up

The first remote run failed to resolve setup-uv's `v10` major alias before any
backend command ran. The published `v10.3.0` release is used explicitly in the
follow-up commit. Frontend unit/lint/build had already passed remotely; browser
and container acceptance are being monitored separately.

Remote lint also exposed a missing executable bit on the benchmark script's
shebang. The file mode is recorded explicitly in Git, including the smoke script,
so fresh Linux checkouts behave consistently.

Container CI confirmed Postgres migration, API readiness, worker health and all
six seed knowledge bases. The frontend started successfully but its BusyBox
wget health probe failed against localhost; it now uses explicit IPv4 loopback
matching Vite's binding. Failure diagnostics include the frontend health log.

After the IPv4 probe fix all long-running containers became healthy. Compose
`up --wait` then treated the successful one-shot seed exit as a failure. Nginx
now declares seed's `service_completed_successfully` dependency, matching the
migration lifecycle, so Compose knows to await completion rather than liveness.
