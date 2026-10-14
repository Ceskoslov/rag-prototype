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
