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
