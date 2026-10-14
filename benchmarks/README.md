# Independent RAG regression corpus

The fixtures are fictional policies with independently written reference
answers and source labels. They cover English, Chinese, Japanese, cross-base
retrieval, distractors, an unanswerable question and an imported injection.
This small corpus is a regression baseline, not a representative quality benchmark.

From `apps/backend` after installing the `dev` extra:

```sh
uv run python scripts/benchmark.py --output /tmp/retrieval-report.json
```

The default checks offline retrieval wiring with deterministic embeddings. It
must not be reported as real semantic retrieval or answer quality. To run real
models, configure both providers and use `--mode rag`; optionally add `--judge`
with the `evaluation` extra installed. These flags call the configured provider.

Reports contain per-case source recall, reciprocal rank, citation number
validity, abstention and latency. Ragas uses complete retrieved passages and
the independent reference answers. Citation number validity does not prove
citation support; the real evidence judge checks support separately.
