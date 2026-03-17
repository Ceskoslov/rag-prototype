# Learnings (2026-03-17)

## LangGraph Persistence
- `AsyncPostgresSaver.from_conn_string()` returns an asynchronous context manager, not a saver instance directly.
- Direct usage in `workflow.compile(checkpointer=...)` leads to `'_AsyncGeneratorContextManager' object has no attribute 'get_next_version'`.
- Use `MemorySaver()` for quick local testing when persistent DB setup is complex.

## Frontend Robustness
- Always use nullish coalescing `?? []` when mapping over data fields that come from an external API, even if the schema suggests they are present.
- A single missing field in a deeply nested trace object can crash the entire React rendering tree.

## SSE Tokenization
- When manually tokenizing a string for SSE streaming (e.g., via `split(" ")`), remember to prepend or append the space character to maintain readable formatting on the frontend.
