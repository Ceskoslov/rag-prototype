# Architectural Decisions — Multi-Agent RAG Project

> Key architectural choices made during planning and implementation.

---

## Planning Phase Decisions

### Memory Management Architecture (2026-03-16)
**Decision**: Three-tier memory system
- **Short-term**: LangGraph State + Message passing within graph execution
- **Medium-term**: AsyncPostgresSaver (LangGraph checkpointing) with `thread_id=session_id`
- **Long-term**: PostgreSQL ConversationRepository + ChromaDB vector knowledge base

**Rationale**: Mirrors human cognitive architecture — working memory (current context), episodic memory (conversation history), semantic memory (knowledge base). LangGraph's checkpointing provides production-grade session isolation.

**Covered By**: Task 28 (checkpointing), Task 13 (conversation persistence), Task 9 (vector ingestion)

---

