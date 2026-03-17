# Issues (2026-03-17)

## Persistent Checkpointer Initialization
- The current implementation in `supervisor.py` uses `MemorySaver()` which resets state upon restart.
- To use `AsyncPostgresSaver`, it needs to be properly initialized within an `async with` block or a similar async initialization pattern before being passed to `workflow.compile`.

## Routing Decision "unknown"
- When `department` is explicitly selected by the user, the `_route_explicit_department` method is called.
- This method bypasses the supervisor's `routing_decision` extraction logic, leading to "unknown" displayed in the trace panel.
- While it doesn't break functionality, it's a UI regression.
