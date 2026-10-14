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
